import chromedriver_autoinstaller

def setup_chromedriver():
    """
    Ensures the correct ChromeDriver version is installed before running bots.
    """
    chromedriver_autoinstaller.install()
