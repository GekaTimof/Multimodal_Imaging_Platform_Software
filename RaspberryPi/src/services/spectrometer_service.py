import time
import threading
import numpy as np
import os
import sys
import logging
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

# Import config
from src.config.settings import config
from .database_service import db_service

# Setup logging
logger = logging.getLogger(__name__)

# Try to import spectrometer connection
try:
    # Add the spectrometer path to sys.path for imports
    spectrometer_path = os.path.join(os.path.dirname(__file__), '..', '..', 'Spectrometer', 'Visualization')
    if spectrometer_path not in sys.path:
        sys.path.insert(0, spectrometer_path)
    
    from SpectrometerOptoskyConnection.SpectrometerConnection import SpectrometerConnection
    from SpectrometerOptoskyConnection.Constants import START_INTEGRAL_TIME, MAX_INTEGRAL_TIME, WAVELENGTH_RANGE_LEN, SPECTRUM_LEN
    SPECTROMETER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Spectrometer module not available: {e}")
    SPECTROMETER_AVAILABLE = False
    START_INTEGRAL_TIME = 100
    MAX_INTEGRAL_TIME = 99999
    WAVELENGTH_RANGE_LEN = 2048
    SPECTRUM_LEN = 2048


class SpectrometerService:
    """Service responsible for capturing spectrum data from the Optosky spectrometer."""

    def __init__(self, fps: int = config.DEFAULT_FPS):
        self.fps: int = fps
        self.spectrum_lock = threading.Lock()
        self.current_wavelength: Optional[np.ndarray] = None
        self.current_spectrum: Optional[np.ndarray] = None
        self.current_real_spectrum: Optional[np.ndarray] = None
        self.dark_spectrum: Optional[np.ndarray] = None
        self.running: bool = False
        self.use_real_spectrometer: bool = False
        self.overillumination: bool = False
        
        # Spectrometer connection
        self.spectrometer: Optional[SpectrometerConnection] = None
        
        # Load settings from database
        self._load_settings()
        
        # Try to initialize spectrometer
        self._initialize_spectrometer()
    
    def _initialize_spectrometer(self):
        """Try to initialize the spectrometer connection."""
        if not SPECTROMETER_AVAILABLE:
            logger.warning("Spectrometer module not available, using test data")
            self.use_real_spectrometer = False
            return
        
        try:
            self.spectrometer = SpectrometerConnection()
            self.spectrometer.open_spectrometer()
            self.spectrometer.retrieve_and_set_wavelength_range()
            self.use_real_spectrometer = True
            logger.info("Spectrometer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize spectrometer: {e}")
            self.use_real_spectrometer = False
    
    def _load_settings(self):
        """Load spectrometer settings from database."""
        try:
            settings = db_service.get_spectrometer_settings()
            if settings:
                self.integral_time = settings.get('IntegralTime', START_INTEGRAL_TIME)
                self.dark_spectrum_path = settings.get('DarkSpectrumPath', '')
                self.auto_dark_correction = settings.get('AutoDarkCorrection', True)
                self.overillumination_threshold = settings.get('OverilluminationThreshold', 65535)
            else:
                # Default settings
                self.integral_time = START_INTEGRAL_TIME
                self.dark_spectrum_path = ''
                self.auto_dark_correction = True
                self.overillumination_threshold = 65535
                
        except Exception as e:
            logger.error(f"Error loading spectrometer settings: {e}")
            # Fallback to default settings
            self.integral_time = START_INTEGRAL_TIME
            self.dark_spectrum_path = ''
            self.auto_dark_correction = True
            self.overillumination_threshold = 65535
    
    def _save_settings(self):
        """Save spectrometer settings to database."""
        try:
            settings = {
                'IntegralTime': self.integral_time,
                'DarkSpectrumPath': self.dark_spectrum_path,
                'AutoDarkCorrection': self.auto_dark_correction,
                'OverilluminationThreshold': self.overillumination_threshold,
                'LastUpdated': datetime.now().isoformat()
            }
            db_service.save_spectrometer_settings(settings)
            logger.info("Spectrometer settings saved to database")
        except Exception as e:
            logger.error(f"Error saving spectrometer settings: {e}")
    
    def start(self):
        """Start the spectrum capture thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Spectrometer service started")
    
    def _capture_loop(self):
        """Main capture loop for spectrum data."""
        while self.running:
            if self.use_real_spectrometer and self.spectrometer:
                try:
                    # Update integral time if changed
                    if self.spectrometer.get_integral_time() != self.integral_time:
                        self.spectrometer.set_integral_time(self.integral_time)
                    
                    # Get new spectrum data
                    self.spectrometer.retrieve_and_set_current_spectrum()
                    
                    with self.spectrum_lock:
                        self.current_wavelength = self.spectrometer.return_wavelength_range().copy()
                        self.current_spectrum = self.spectrometer.return_current_spectrum().copy()
                        self.current_real_spectrum = self.spectrometer.return_real_current_spectrum().copy()
                        
                        # Check for overillumination
                        self.spectrometer.check_overillumination()
                        self.overillumination = self.spectrometer.return_overillumination()
                        
                except Exception as e:
                    logger.error(f"Spectrometer capture error: {e}")
                    self.use_real_spectrometer = False
            else:
                # Generate test data
                with self.spectrum_lock:
                    self._generate_test_spectrum()
            
            time.sleep(1 / self.fps)
    
    def _generate_test_spectrum(self):
        """Generate test spectrum data."""
        # Create wavelength range (typical for spectrometers)
        self.current_wavelength = np.linspace(200, 800, WAVELENGTH_RANGE_LEN)
        
        # Create a synthetic spectrum with some peaks
        x = self.current_wavelength
        # Simulate some spectral peaks
        spectrum = (
            1000 * np.exp(-((x - 450) / 20) ** 2) +  # Blue peak
            1500 * np.exp(-((x - 550) / 25) ** 2) +  # Green peak
            800 * np.exp(-((x - 650) / 30) ** 2) +   # Red peak
            100 * np.sin(x / 50) +  # Some oscillation
            200  # Baseline
        )
        
        # Add some noise
        noise = np.random.normal(0, 50, len(x))
        spectrum += noise
        
        # Ensure non-negative values
        spectrum = np.maximum(spectrum, 0)
        
        self.current_spectrum = spectrum.astype(np.uint16)
        
        # Apply dark correction if available
        if self.dark_spectrum is not None and len(self.dark_spectrum) == len(spectrum):
            self.current_real_spectrum = np.maximum(spectrum - self.dark_spectrum, 0)
        else:
            self.current_real_spectrum = self.current_spectrum.copy()
        
        # Check for overillumination
        self.overillumination = bool(np.max(self.current_spectrum) >= self.overillumination_threshold)
    
    def get_spectrum_data(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray]]:
        """Get current spectrum data (wavelength, raw spectrum, corrected spectrum)."""
        with self.spectrum_lock:
            return (
                self.current_wavelength.copy() if self.current_wavelength is not None else None,
                self.current_spectrum.copy() if self.current_spectrum is not None else None,
                self.current_real_spectrum.copy() if self.current_real_spectrum is not None else None
            )
    
    def set_dark_spectrum(self) -> bool:
        """Capture and set dark spectrum."""
        if not self.use_real_spectrometer or not self.spectrometer:
            logger.warning("Cannot set dark spectrum: spectrometer not available")
            return False
        
        try:
            self.spectrometer.retrieve_and_set_dark_spectrum()
            with self.spectrum_lock:
                self.dark_spectrum = self.spectrometer.return_dark_spectrum().copy()
            
            # Save dark spectrum to file
            self._save_dark_spectrum_file()
            logger.info("Dark spectrum captured and saved")
            return True
        except Exception as e:
            logger.error(f"Failed to capture dark spectrum: {e}")
            return False
    
    def clear_dark_spectrum(self):
        """Clear the dark spectrum."""
        with self.spectrum_lock:
            self.dark_spectrum = None
        
        if self.use_real_spectrometer and self.spectrometer:
            try:
                self.spectrometer.clear_dark_spectrum()
            except Exception as e:
                logger.error(f"Failed to clear dark spectrum in spectrometer: {e}")
        
        # Clear saved path
        self.dark_spectrum_path = ''
        self._save_settings()
        logger.info("Dark spectrum cleared")
    
    def _save_dark_spectrum_file(self):
        """Save dark spectrum to file on Raspberry Pi."""
        if self.dark_spectrum is None:
            return
        
        try:
            # Create directory for dark spectra if it doesn't exist
            dark_spectra_dir = os.path.join(config.DATA_DIR, 'dark_spectra')
            os.makedirs(dark_spectra_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dark_spectrum_{timestamp}.npy"
            filepath = os.path.join(dark_spectra_dir, filename)
            
            # Save as numpy array
            np.save(filepath, self.dark_spectrum)
            
            # Also save as text file for compatibility
            txt_filepath = os.path.join(dark_spectra_dir, f"dark_spectrum_{timestamp}.txt")
            np.savetxt(txt_filepath, self.dark_spectrum, fmt='%d')
            
            # Update settings
            self.dark_spectrum_path = filepath
            self._save_settings()
            
            logger.info(f"Dark spectrum saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save dark spectrum file: {e}")
    
    def load_dark_spectrum_file(self, filepath: str) -> bool:
        """Load dark spectrum from file."""
        try:
            if filepath.endswith('.npy'):
                self.dark_spectrum = np.load(filepath)
            else:
                self.dark_spectrum = np.loadtxt(filepath, dtype=np.uint16)
            
            # Update spectrometer if available
            if self.use_real_spectrometer and self.spectrometer:
                # Note: The original spectrometer connection doesn't have a method to set dark spectrum directly
                # We'll store it internally and apply correction in our service
                pass
            
            self.dark_spectrum_path = filepath
            self._save_settings()
            logger.info(f"Dark spectrum loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load dark spectrum from {filepath}: {e}")
            return False
    
    def set_integral_time(self, integral_time: int) -> bool:
        """Set the integration time."""
        if not (1 <= integral_time <= MAX_INTEGRAL_TIME):
            logger.error(f"Invalid integral time: {integral_time}. Must be between 1 and {MAX_INTEGRAL_TIME}")
            return False
        
        self.integral_time = integral_time
        
        if self.use_real_spectrometer and self.spectrometer:
            try:
                self.spectrometer.set_integral_time(integral_time)
                logger.info(f"Integration time set to {integral_time}")
            except Exception as e:
                logger.error(f"Failed to set integration time: {e}")
                return False
        
        self._save_settings()
        return True
    
    def get_spectrometer_info(self) -> Dict[str, Any]:
        """Get spectrometer information."""
        info = {
            'connected': self.use_real_spectrometer,
            'integral_time': self.integral_time,
            'dark_spectrum_loaded': self.dark_spectrum is not None,
            'dark_spectrum_path': self.dark_spectrum_path,
            'auto_dark_correction': self.auto_dark_correction,
            'overillumination': self.overillumination,
            'overillumination_threshold': self.overillumination_threshold
        }
        
        if self.use_real_spectrometer and self.spectrometer:
            try:
                self.spectrometer.set_session_info()
                info.update({
                    'vendor': self.spectrometer.return_vendor(),
                    'pn': self.spectrometer.return_pn(),
                    'sn': self.spectrometer.return_sn(),
                    'module_version': self.spectrometer.return_module_version(),
                    'production_date': self.spectrometer.return_module_production_date()
                })
            except Exception as e:
                logger.error(f"Failed to get spectrometer info: {e}")
        
        return info
    
    def reload_settings(self):
        """Reload spectrometer settings from database."""
        old_integral_time = self.integral_time
        self._load_settings()
        
        # Update spectrometer if integral time changed
        if old_integral_time != self.integral_time and self.use_real_spectrometer and self.spectrometer:
            try:
                self.spectrometer.set_integral_time(self.integral_time)
                logger.info(f"Integral time updated to {self.integral_time}")
            except Exception as e:
                logger.error(f"Failed to update integral time: {e}")
    
    def stop(self):
        """Stop spectrometer service."""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        
        # Close spectrometer connection
        if self.use_real_spectrometer and self.spectrometer:
            try:
                # Note: The original spectrometer connection doesn't have an explicit close method
                # The connection will be closed when the process terminates
                pass
            except Exception as e:
                logger.error(f"Error closing spectrometer: {e}")
        
        logger.info("Spectrometer service stopped")