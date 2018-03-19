#!/bin/bash

# Pre-requirements for pycift


# Goto the home directory
cd ~


# Install Brew & NPM
ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" < /dev/null 2> /dev/null
brew install caskroom/cask/brew-cask 2> /dev/null
#brew install npm


# Install Google Chrome
echo "==========================="
echo "Installing Chrome ..."
echo "==========================="
#brew cask install google-chrome


# Install ChromeDriver
echo "==========================="
echo "Installing ChromeDriver ..."
echo "==========================="
brew install chromedriver
brew upgrade chromedriver

#cd $HOME/Downloads
#LATEST=$(wget -q -O - http://chromedriver.storage.googleapis.com/LATEST_RELEASE)
#wget -N http://chromedriver.storage.googleapis.com/$LATEST/chromedriver_mac64.zip
#unzip chromedriver_mac64.zip
#mkdir -p $HOME/bin
#mv chromedriver $HOME/bin
#echo "export PATH=$PATH:$HOME/bin" >> $HOME/.bash_profile


# Install PhantomJS
echo "==========================="
echo "Installing PhantomJS ..."
echo "==========================="
brew install phantomjs
#npm install -g phantomjs-prebuilt


#echo "==========================="
#echo "Install Selenium and python dependencies ..."
#echo "==========================="
#pip3 install --upgrade pip
#pip3 install pyvirtualdisplay selenium
#pip3 install python-dateutil peewee requests construct iso8601
