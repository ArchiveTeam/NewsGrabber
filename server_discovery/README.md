# NewsGrabber Discovery

Discovery scripts to be used in combination with the main and grabber scripts of NewsGrabber. This discovery script can be managed from IRC using the commands listed in this README.

Setup
-----
To run these scripts you need to have `rsync` and for python `requests` installed and set up.
A file `target` with the rsync target of the main server needs to be created and located in the server_discovery dir.

Discovered URLs
---------------
For each discovered URLs the following information is stored. This information is send the the main server as JSON file when new URLslists are synced.

* `url`: New URL.

* `script_version`: Version of the current running discovery scripts.

* `service_version`: Version of the service script the URL was discovered for.

* `service_url`: The seedURL in the URL was discovered in.

* `sort`: The kind of URL. Can have values `video` and `normal`.

* `live`: `True` if URL is a liveURL, else `False`.

* `time`: Unixtime the URL was added to the new URLslist.

* `immediate_grab`: `True` if URL needs to be grabbed immediatly, else `False`.

* `bot_nick`: Nickname of the discovery server.

IRC Commands
------------
The discovery server can be managed through IRC. Available commands are listed here.

`{discovery_server}` is the name of the discovery server given by the main server, `global` for all servers, or the global discovery servers name `discovery`, `disco` or `discoverer`.

`{service_id}` is the name of a service. For example `web__7days_ae`.

* `!status`: Get the status of the running scripts. Get an overview of whether all parts  of the discovery are still running.

* `!info {service_id}` / `information {service_id}`: Check if the discovery server is running this service.

* `!clear {discovery_server}`: Clear the lists currently stored on the server. The lists of discovered URLs for deduplication on the discovery server are emptied. New found URLs will still be deduplicated on the main server.

* `!version {discovery_server}`: Get the current used version of the discovery scripts.

* `!pause {discovery_server}`: Pause the discovery of new URLs and upload of new URLslists to the main server.

* `!resume {discovery_server}`: Resume the discovery of new URLs and upload of new URLslists to the main server. Can be used after only `!pause-upload` or `!pause-grab`.

* `!pause-upload {discovery_server}`: Pause the upload of new URLslists to the main server.

* `!resume-upload {discovery_server}`: Resume the upload of new URLslists to the main server.

* `!pause-grab {discovery_server}`: Pause the discovery of new URLs.

* `!resume-grab {discovery_server}`: Resume the discovery of new URLs.

* `!refresh {discovery_server} option`: `option` shall be `default` or be in seconds. Set a global discovery refresh time with a value in seconds for `option`. If a server has a default refresh time lower than the set global refresh time, the new refresh time is ignored for this service. To go back to the defaults of the services, use `default` for `option`.

* `!EMERGENCY_STOP {discovery_server}`: Stop the scripts. Can only be undone by manually restarting the scripts.
