import os
import pexpect
import numpy as np

from SpectrometerOptoskyConnection.Constants import OVERILLUMINATION_THRESHOLD, MINIMUM_WAITING_TIME, WAITING_TIME_MULTIPLIER, SPECTROMETER_DIR, SPECTROMETER_FILE, START_INTEGRAL_TIME, WAVELENGTH_RANGE_LEN, SPECTRUM_LEN
from SpectrometerOptoskyConnection.Constants import OptoskySpectrometerCommands, Command_get_modul_production_date, Command_get_modul_version, Command_get_SN, Command_get_PN, Command_get_vendor, Command_open_spectrometer, Command_get_wavelength_range, Command_get_dark_spectrum, Command_get_current_spectrum

# class that contain spectrometer connection
class SpectrometerConnection:
    def __init__(self):
        # set dict os spectrometer commands
        # {"key": ("id", [key_text_1, key_text_2, ...])}
        self.Commands = OptoskySpectrometerCommands

        # set spectrometer commands
        self.Open_spectrometer = Command_open_spectrometer
        self.Get_wavelength_range = Command_get_wavelength_range
        self.Get_dark_spectrum = Command_get_dark_spectrum
        self.Get_current_spectrum = Command_get_current_spectrum
        self.Get_vendor = Command_get_vendor
        self.Get_PN = Command_get_PN
        self.Get_SN = Command_get_SN
        self.Get_modul_version = Command_get_modul_version
        self.Get_modul_production_date = Command_get_modul_production_date

        # set start accumulation time
        self.integral_time: int = START_INTEGRAL_TIME
        # set start waiting for response time
        self.waiting_time = self.integral_time * WAITING_TIME_MULTIPLIER

        # set wavelength len and empty wavelength array
        self.wavelength_range_len: int = WAVELENGTH_RANGE_LEN
        self.wavelength_range = np.zeros(self.wavelength_range_len)

        # set spectrum len and empty spectrum array
        self.spectrum_len: int = SPECTRUM_LEN
        self.dark_spectrum = np.zeros(self.spectrum_len)
        self.current_spectrum = np.zeros(self.spectrum_len)
        self.real_current_spectrum = np.zeros(self.spectrum_len)

        # set sub parameter (True - is we set dark spectrum, False - is we don't set dark spectrum )
        self.sub = False
        # set over-illumination parameter
        self.overillumination = False

        # info about spectrometer
        self.vendor = ''
        self.PN = ''
        self.SN = ''
        self.module_version = ''
        self.module_production_date = ''

        # set working directory
        self.working_directory = SPECTROMETER_DIR
        if not os.path.exists(self.working_directory):
            raise FileNotFoundError(f"Spectrometer directory not found: {self.working_directory}")

        # set path to spectrometer script
        self.spectrometer_path = SPECTROMETER_FILE
        if not os.path.isfile(self.spectrometer_path):
            raise FileNotFoundError(f"Spectrometer script not found: {self.spectrometer_path}")

        # set spectrometer connection proses
        self.process = pexpect.spawn(f'{self.spectrometer_path}', cwd=self.working_directory, encoding="utf-8", timeout=10)


    # method return spectrometer working_directory
    def get_working_directory(self):
        return self.working_directory


    # method return spectrometer accumulation time
    def get_integral_time(self):
        return self.integral_time


    # method set spectrometer accumulation time
    def set_integral_time(self, new_integral_time: int):
        if new_integral_time > 0:
            self.integral_time = new_integral_time
            self.waiting_time = new_integral_time * WAITING_TIME_MULTIPLIER
        else:
            raise Exception(f"an able to set integral_time = {new_integral_time}")


    # method send one command to spectrometer
    def send_command(self, command: str):
        self.process.sendline(command)
        return self


    # method trying to find expect_answer in spectrometer text flow
    def wait_for_response(self,  expect_answer: str, waiting_time: int):
        waiting_time = max(waiting_time, MINIMUM_WAITING_TIME)
        try:
            # wait for answer
            self.process.expect(expect_answer, timeout=waiting_time)
        except:
            raise Exception(f"No answer '{expect_answer}' from spectrometer")


    # method trying to find expect_answer in spectrometer text flow and return all test before it
    def read_until_response(self,  expect_answer: str, waiting_time: int):
        waiting_time = max(waiting_time, MINIMUM_WAITING_TIME)
        # wait for answer
        self.wait_for_response(expect_answer, waiting_time=waiting_time)

        # get response
        response = self.process.before
        return response


    # method to connect to spectrometer
    def open_spectrometer(self):
        # get command parameters
        command_id = self.Commands[self.Open_spectrometer][0]
        expected_answers = self.Commands[self.Open_spectrometer][1]

        # try to connect
        try:
            self.send_command(command_id)
            # checking connection
            self.wait_for_response(expected_answers[0], MINIMUM_WAITING_TIME)
            # skip before next request
            self.wait_for_response(expected_answers[1], MINIMUM_WAITING_TIME)
        except:
            raise Exception(f"Can't connect to spectrometer")
        return self


    # method to split text data for len lince and convert to np array
    def split_spectrometer_response(self, response: str, data_len: int):
        lines = response.split('\n')
        # List to store extracted data
        data = []

        # try to convert text to float
        for line in lines:
            # Ignore empty lines or lines without tab
            if line.strip() and "\t" in line:
                # Try to extract the second number
                try:
                    # Extract number after tab
                    value = float(line.split("\t")[1].strip())
                    data.append(value)
                except ValueError:
                    pass  # Skip lines that don't have a valid number

        # Convert list to numpy array
        data = np.array(data, dtype=np.float32)

        # check array total len
        if len(data) != data_len:
            return None
        return data


    def check_overillumination(self):
        self.overillumination = np.max(self.current_spectrum) >= OVERILLUMINATION_THRESHOLD


    # method to retrieve and set wavelength range
    def retrieve_and_set_wavelength_range(self):
        # get command parameters
        command_id = self.Commands[self.Get_wavelength_range][0]
        expected_answers = self.Commands[self.Get_wavelength_range][1]

        # send command
        self.send_command(command_id)

        # checking that the wavelength range has been received
        self.wait_for_response(expected_answers[0], MINIMUM_WAITING_TIME)
        # get data from response
        response = self.read_until_response(expected_answers[1], MINIMUM_WAITING_TIME)
        data = self.split_spectrometer_response(response, self.wavelength_range_len)

        # set wavelength range if we got it
        if data is not None:
            self.wavelength_range = data

        # skip before next request
        self.wait_for_response(expected_answers[2], MINIMUM_WAITING_TIME)
        return self


    # method to retrieve and set dark spectrum
    def retrieve_and_set_dark_spectrum(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_dark_spectrum][0]
        expected_answers = self.Commands[self.Get_dark_spectrum][1]

        # send command
        self.send_command(command_id)

        # wait for integral time request
        self.wait_for_response(expected_answers[0], waiting_time)
        # send integral time
        self.send_command(str(self.integral_time))

        # checking that the integral time has been set and data has been received
        self.wait_for_response(expected_answers[1], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[2], waiting_time)
        data = self.split_spectrometer_response(response, self.spectrum_len)
        # set dark spectrum if we got
        if data is not None:
            self.dark_spectrum = data
            self.sub = True
            # set new real current spectrum
            self.real_current_spectrum = self.current_spectrum - self.dark_spectrum

        # skip before next request
        self.wait_for_response(expected_answers[3], waiting_time)
        return self


    # method to retrieve and set current spectrum
    def retrieve_and_set_current_spectrum(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_current_spectrum][0]
        expected_answers = self.Commands[self.Get_current_spectrum][1]

        # send command
        self.send_command(command_id)

        # wait for integral time request
        self.wait_for_response(expected_answers[0], waiting_time)
        # send integral time
        self.send_command(str(self.integral_time))

        # checking that the integral time has been set and data has been received
        self.wait_for_response(expected_answers[1], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[2], waiting_time)
        data = self.split_spectrometer_response(response, self.spectrum_len)
        # set current spectrum if we got
        if data is not None:
            self.current_spectrum = data
            # set new real current spectrum
            self.real_current_spectrum = self.current_spectrum - self.dark_spectrum

        # skip before next request
        self.wait_for_response(expected_answers[3], waiting_time)
        return self


    # method to retrieve and set vendor
    def retrieve_and_set_vendor(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_vendor][0]
        expected_answers = self.Commands[self.Get_vendor][1]

        # send command
        self.send_command(command_id)
        # wait for response
        self.wait_for_response(expected_answers[0], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[1], waiting_time)
        # set vendor
        self.vendor = response.strip()
        # skip before next request
        self.wait_for_response(expected_answers[2], waiting_time)
        return self


    # method to retrieve and set PN
    def retrieve_and_set_PN(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_PN][0]
        expected_answers = self.Commands[self.Get_PN][1]

        # send command
        self.send_command(command_id)
        # wait for response
        self.wait_for_response(expected_answers[0], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[1], waiting_time)
        # set vendor
        self.PN = response.strip()
        # skip before next request
        self.wait_for_response(expected_answers[2], waiting_time)
        return self


    # method to retrieve and set SN
    def retrieve_and_set_SN(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_SN][0]
        expected_answers = self.Commands[self.Get_SN][1]

        # send command
        self.send_command(command_id)
        # wait for response
        self.wait_for_response(expected_answers[0], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[1], waiting_time)
        # set vendor
        self.SN = response.strip()
        # skip before next request
        self.wait_for_response(expected_answers[2], waiting_time)
        return self


    # method to retrieve and set module version
    def retrieve_and_set_module_version(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_modul_version][0]
        expected_answers = self.Commands[self.Get_modul_version][1]

        # send command
        self.send_command(command_id)
        # wait for response
        self.wait_for_response(expected_answers[0], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[1], waiting_time)
        # set vendor
        self.module_version = response.strip()
        # skip before next request
        self.wait_for_response(expected_answers[2], waiting_time)
        return self


    # method to retrieve and set module production date
    def retrieve_and_set_module_production_date(self):
        # time we wait for data (seconds)
        waiting_time = self.waiting_time / 1000

        # get command parameters
        command_id = self.Commands[self.Get_modul_production_date][0]
        expected_answers = self.Commands[self.Get_modul_production_date][1]

        # send command
        self.send_command(command_id)
        # wait for response
        self.wait_for_response(expected_answers[0], waiting_time)
        # get data from response
        response = self.read_until_response(expected_answers[1], waiting_time)
        # set vendor
        self.module_production_date = response.strip()
        # skip before next request
        self.wait_for_response(expected_answers[2], waiting_time)
        return self


    # method to set all info about session
    def set_session_info(self):
        self.retrieve_and_set_vendor()
        self.retrieve_and_set_PN()
        self.retrieve_and_set_SN()
        self.retrieve_and_set_module_version()
        self.retrieve_and_set_module_production_date()


    # method to clear dark spectrum
    def clear_dark_spectrum(self):
        self.dark_spectrum = np.zeros(self.spectrum_len)
        self.sub = False
        self.real_current_spectrum = self.current_spectrum - self.dark_spectrum


    # method return current integral time
    def return_integral_time(self):
        return self.integral_time


    # method return wavelength range
    def return_wavelength_range(self):
        return self.wavelength_range


    # method return dark spectrum
    def return_dark_spectrum(self):
        return self.dark_spectrum


    # method return current spectrum
    def return_current_spectrum(self):
        return self.current_spectrum


    # method return real current spectrum
    def return_real_current_spectrum(self):
        return self.real_current_spectrum


    # method return (wavelength range and real current spectrum)
    def return_wavelength_and_spectrum(self):
        return (self.wavelength_range, self.real_current_spectrum)


    # method return sub parameter
    def return_sub_parameter(self):
        return self.sub


    # method return spectrometer vendor
    def return_vendor(self):
        return self.vendor


    # method return spectrometer PN
    def return_pn(self):
        return self.PN


    # method return spectrometer SN
    def return_sn(self):
        return self.SN


    # method return spectrometer module version
    def return_module_version(self):
        return self.module_version


    # method return spectrometer module production date
    def return_module_production_date(self):
        return self.module_production_date


    # method return sub parameter
    def return_sub_parameter_text(self):
        if self.sub:
            return "sub"
        else:
            return "no_sub"


    # method return overillumination parameter
    def return_overillumination(self):
        return self.overillumination


    # method return array with information about session and spectrometer
    def return_session_info(self):
        self.set_session_info()
        info = []
        info.append(self.return_sub_parameter_text())
        info.append(f"integral_time: {self.return_integral_time()}")
        info.append(f"{self.return_vendor()}")
        info.append(f"{self.return_pn()}")
        info.append(f"{self.return_sn()}")
        info.append(f"{self.return_module_version()}")
        info.append(f"{self.return_module_production_date()}")
        return info


if __name__ == "__main__":
    connection = SpectrometerConnection()
    connection.open_spectrometer()
