# NewsGrabber Main

Main scripts to be used in combination with the discovery and grabber scripts of NewsGrabber. This main script can be managed from IRC using the commands listed in this README.

Setup
-----
To run these scripts you need to have `rsync` and `internetarchive` and for python `requests`, `psutil` and `pytz` installed and set up. To install the dependencies:
```
sudo apt-get install gcc python-dev python-pip rsync internetarchive
sudo pip install psutil requests pytz
```

IRC Commands
------------
The main server can be managed through IRC. Available commands are listed here.

`{main_server}` is the name of the main server, `main` or `storage` for the main server or `global` for all servers.

`{service_id}` is the name of a service. For example `web__7days_ae`. Needs to start with `web__`.

`{URL}` is an URL.

* `!help`: Get help information.
* `!server-stats {main_server}`: Get statistics on the system. Given statistics are:
  * CPU usage percent:
    * `total`
    * `user`
    * `nice`
    * `system`
    * `idle`
  * Virtual memory usage:
    * `total`
    * `percent`
  * Disk usage:
    * `total`
    * `percent`
* `!handle-targets`: Add, remove and change grab and discovery targets. IN DEVELOPMENT.
* `!stop`: Runs `!writefiles` and stops the scripts. Scripts can only be restarted manually.
* `!pause {main_server}`: Pause the sorting and uploading of URLs and upload of WARCs.
* `!resume {main_server}`: Resume the sorting and uploading of URLs and upload of WARCs.
* `!pause-urls`: Pause the sorting and uploading of URLs.
* `!resume-urls`: Resume the sorting and uploading of URLs.
* `!pause-upload {main_server}`: Pause the upload of WARCs.
* `!resume-upload {main_server}`: Resume the upload of WARCs.
* `!version {main_server}`: Get the current used version of the main scripts.
* `!writefiles`: Write JSON files of the discovered URLs. These JSON files will be loaded if the scripts are restarted.
* `!cu {main_server}` / `!con-uploads {main_server}` / `!concurrent_uploads {main_server}`: Set the maximum concurrent upload of WARCs.
* `!rs` / `!refresh-services`: Refresh the service files and upload new service lists to the discoverers. Services will be synced from GitHub.
* `!info {service_id}` / `!information {service_id}`: Check if the service exists. If the service exists, the following information of the service is given:
  * Service name
  * Service script version
  * Refresh time
  * SeedURLs
  * Regex for normal URLs
  * Regex for video URLs
  * Regex for live URLs
  * ID of the website on Wikidata
  * Number of URLs grabbed for this service
* `!info {URL}` / `!information {URL}`: Get the corresponding service. If the URL has been grabbed and loaded in memory the following information of the first time the URL was found is given:
  * Number of times the URL was grabbed
  * When the URL was first found
  * Which discovery server found the URL
  * In which service the URL was found
  * In which seedURL the URL was found
  * With which version of the service the URL was found
  * With which version of the discovery script the URL was found
  * The kind of URL (`video` or `normal`)
  * If this is a live URL
  * If this URL was grabbed immediatly
* `!EMERGENCY_STOP`: Stop the scripts. Scripts can only be restarted manually.
