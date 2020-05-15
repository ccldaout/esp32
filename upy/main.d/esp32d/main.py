from config.boot_full import config
import hd44780


config.ssd1331 = False
config.progress_ssd1331 = False


def main():
    global lcd
    lcd = hd44780.HD44780(hd44780.GPIO())
