# Boardgame-Bot

Here is a Boardgame Bot under Construction.

OLD Code can be found in the OLD-GScript Folder so far 

new one has no Structure yet.

If you want to test the Code locally you may do so but have to meet the requirements.

    - Python 2.xx oder 3.xx 
    - telepot

Quick Start: 
 -
 
To get started locally I recommend not just installing python (duh)
but also to use an IDE that helps with formatting and testing.

For this reason I use [**PyCharm**](https://www.jetbrains.com/pycharm/)

to install telepot pip should also be installed:

```shell
sudo apt-get install python-pip
sudo pip install telepot
```

afterwards we may test if telepot is working by executing inside an Python Environment:

``` Shell
import telepot
bot = telepot.Bot('*** copy bot token from browser ***')
bot.getMe()
```

And that's it!

Now you are good to go and may start working on our lovely bot!
