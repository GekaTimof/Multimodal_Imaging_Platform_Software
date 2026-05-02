# Запуск приложения
## Запуск с запросом пароля
Установка зависимостей для пользователя, выполнить кманду:

    pip3 install --user -r requirements.txt


В файл run.sh написать путь запуска программы:

    \#!/bin/bash
    sudo python3 путь_к/Visualisation/main.py


## Запуск без пароля
Получить имя пользователя, выполните команду:

    whoami


Установка зависимостей для sudo, выполнить кманду:

    sudo pip3 install -r requirements.txt


Получить расположение python3, выполним команду:

    which python3


Установить разрешение запуска без пароля, выполните команду:
    
    sudo visudo

    
В самом конце файла добавьте строку:

    имя_пользователя ALL=(ALL) NOPASSWD: путь_к_/python3 путь_к/Visualisation/main.py
*Подставте пути к файлу python3 и main.py 


В файл run.sh заменить строчку на:

    sudo путь_к_/python3 путь_к/Visualisation/main.py
*Подставте пути к файлу python3 и main.py 


Запрет редактирования файлов программы в Spectrometer

    sudo chmod -R 755 Spectrometer


Разрешаем редактирование файлов нужныйх для кастомизации приложения

    sudo chattr -i /Visualization/SpectrometerApplication и открыть файл Constants.py



## Создание ярлыка

Откройте терминал и введите:

    nano ~/.local/share/applications/spectrometer.desktop

Вставьте в открывшийся файл следующее содержимое:
    
    [Desktop Entry]
    Name=Spectrometer
    Comment=Spectrometer Visualization Tool
    Exec=путь_к/run.sh
    Icon=путь_к/Visualization/Assets/icon.png
    Terminal=false
    Type=Application
    Categories=Utility;
*Подставте пути к файлу run.sh и icon.png

Сохраните:

    Нажмите Ctrl + O, затем Enter
    Выйдите: Ctrl + X

    
Сделайте run.sh и .desktop исполняемыми:

    chmod +x путь_к/run.sh
    chmod +x ~/.local/share/applications/spectrometer.desktop    
*Подставте пути к файлу run.sh    
    
 
    
# Настройка приложения под себя
## Настройка папки сохранения и загрузки спектральных файлов
Перейти в папку **/Visualization/SpectrometerApplication и открыть файл Constants.py**

Найти строку **BASE_FILES_DIR = "..."**

Вписать в нужный путь **вместо "..."**


## Настройка темы по умолчанию
Перейти в папку **/Visualization/SpectrometerApplication и открыть файл Constants.py**

Найти строку **DARK_THEME = "..."**

Что-бы установить тёмную тему по умолчанию, впишите True **вместо "..."**

Что-бы установить светлую тему по умолчанию, впишите False **вместо "..."**


## Настройка шрифтов
Перейти в папку **/Visualization/SpectrometerApplication и открыть файл Constants.py**

Для настройки шрифтов можете изменить следующие параметры, заменяя **"..."** на своё значение:

**FONT_SIZE = "..."** -> размер ткста кнопок (чисто)

**FONT = "..."** -> шрифт всего текста (название шрифта)

**WARNING_FONT_SIZE = "..."** -> размер текста предупреждения  пересвете

**COORDINATES_FONT_SIZE = "..."** -> размер текста координат мыши

    
## Настройка отображения линии спектра на графике
Перейти в папку **/Visualization/SpectrometerApplication и открыть файл Constants.py**

Для настройки отображения линии спектра на графике можете изменить следующие параметры, заменяя **"..."** на своё значение



# Информация для отладки
Что-бы посмотреть ошибки и информацию о них, необходимо запустить приложение через консоль

./Visualization/run.sh

После зпуска в консоль будет выводиться информация о появившихся ошибках 
