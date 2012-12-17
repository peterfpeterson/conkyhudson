How to Install
==============

Pre-requites:
-------------
Python 2.6.4
conky

Instructions
------------
1. Download ConkyHudson

2. Untar in a directory of your choosing

These files do not extract in a directory of their own! I suggest extracting to .conkyhudson

3. Set up your conkyHudson.template
More information can be found on the
[template](https://github.com/Ronnie76er/conkyhudson/wiki/template-formatting) formatting page 

4. Set up conky to use conkyHudson

This is accomplished by adding the following line to your .conkyrc in your home directory:

> ${execpi 10 /home/ronnie/.conkyhudson/conkyhudson.py -t /home/ronnie/.conkyhudson/conkyHudson.template}

And that’s it! You’re all set!
