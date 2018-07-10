temperpi
========

RaspberryPi Temperature Monitor with Temper2 (server+client)



How To Setup The Server
========

1. Get a server with Ubuntu installed. (in my case, I'm using one from AWS EC2)

2. Run the following commands in bash:

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


