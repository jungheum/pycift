#!/bin/bash

# Pre-requirements for pycift
# (it assumes python3 is available at /usr/bin/python3)


# Goto the home directory
cd ~


echo "==========================="
echo "Updating 'apt-get' ..."
echo "==========================="
sudo apt-get update
sudo apt-get install build-essential chrpath libssl-dev libxft-dev -y
sudo apt-get install libfreetype6 libfreetype6-dev -y
sudo apt-get install libfontconfig1 libfontconfig1-dev -y


# Install Google Chrome
echo "==========================="
echo "Installing Chrome ..."
echo "==========================="
sudo apt-get install libxss1 libappindicator1 libindicator7
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i --force-depends google-chrome-stable_current_amd64.deb


# Install ChromeDriver
echo "==========================="
echo "Installing ChromeDriver ..."
echo "==========================="
sudo apt-get install unzip
LATEST=$(wget -q -O - http://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -N http://chromedriver.storage.googleapis.com/$LATEST/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
chmod +x chromedriver
sudo mv -f chromedriver /usr/local/bin/chromedriver


# Install PhantomJS
echo "==========================="
echo "Installing PhantomJS ..."
echo "==========================="
export PHANTOM_JS="phantomjs-2.1.1-linux-x86_64"
wget https://github.com/Medium/phantomjs/releases/download/v2.1.1/$PHANTOM_JS.tar.bz2
sudo tar xvjf $PHANTOM_JS.tar.bz2
sudo mv $PHANTOM_JS /usr/local/share
sudo ln -sf /usr/local/share/$PHANTOM_JS/bin/phantomjs /usr/local/bin


# Install headless GUI 'Xvfb' (a display server that performs graphical operations in memory)
echo "==========================="
echo "Installing XVFB (headless GUI) ..."
echo "==========================="
sudo apt-get install xvfb


#echo "==========================="
#echo "Install Selenium and python dependencies ..."
#echo "==========================="
#sudo apt-get install python3-pip
#pip3 install --upgrade pip
#pip3 install pyvirtualdisplay selenium
#pip3 install python-dateutil peewee requests construct iso8601
