temperpi
========

RaspberryPi Temperature Monitor with Temper2 (server+client)


How To Setup The Server
========

1. Get a server with Ubuntu installed. (in my case, I'm using one from AWS EC2)

2. Git clone the repository into */home/ubuntu/Sandbox/temperpi/*.

3. Run the following commands in bash:

```
# Install all required packages.
sudo apt-get install python pip
sudo pip install cherrypy python-dateutil mako

# Configure the service in /etc/init.d.
sudo ln -s /home/ubuntu/Sandbox/temperpi/server/temperpi.server.sh /etc/init.d/temperpi
sudo /etc/init.d/temperpi start
sudo systemctl enable temperpi
service --status-all
```

After this, the server should be happily running under http://localhost:4284.


How To Setup The Client
========

1. Configure a new RaspberryPi with Raspbian and plug in the Temper2 USB thermometre.

2. Git clone the repository into *~/Sandbox/temperpi/*.

3. Install required packages for the C compilation:

```
sudo apt-get install libusb-dev
```

4. Run the following commands to compile temper2.

```
cd ~/Sandbox/temperpi/client/TEMPer2/
make
```

5. Add the the send.sh command to your root crontab. (the binary produced above needs to run as root)

```
sudo crontab -e
```

And add a line that looks like the one below updating the server url to wherever your actual server is located at.

```
* * * * * /home/ruibm/Sandbox/temperpi/client/send.sh 'http://my.server.url:4284'
```
