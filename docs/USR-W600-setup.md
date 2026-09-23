# USR-W600: redirect an ES heat pump to Home Assistant

[Русская инструкция](USR-W600-setup.ru.md) · [README](../README.md)

Adapted from the ES **Wi-Fi connection** guide, filename **2020118 RM Wi-Fi instlation manual, ver2.pdf**, pages 3–9. Field names were checked against its screenshots. The manufacturer's guide configures the cloud destination; using Home Assistant instead is this project's adaptation, verified on the original USR-W600 installation only. The PDF is not redistributed here.

## Prepare Home Assistant

Install and add the integration as described in the README. Use bind address `0.0.0.0` and TCP port `18899`. Reserve a stable LAN IPv4 address for the HA host. The module must be able to reach that port, including across any firewall/VLAN or container boundary. For Docker, publish `18899:18899/tcp` or provide equivalent network access.

The receiver has no authentication/TLS: use a trusted LAN, without internet port forwarding.

## Redirect an already connected module

1. Find the module's current LAN IP in your router's client list. Its MAC is shown on the heat pump controller under **Other options**, page 4 (manual p. 9).
2. Open the module's web interface at that IP. Use its current credentials. The manual lists factory credentials `admin` / `admin`; these apply only if unchanged.
3. Privately save screenshots of the existing Wi-Fi, serial and socket configuration for rollback. Select **English** if necessary.
4. Open **Trans Setting → SocketB Connect Setting**. Do not confuse it with Socket A above it.
5. Set the following fields, then select **Save → Restart** to restart the Wi-Fi module and apply them.

| Field | Vendor cloud configuration | Local HA configuration |
| --- | --- | --- |
| Network Setting → Mode | `Transparent` in manual screenshot | Keep `Transparent` |
| Socket B → Protocol | `TCP-Client` | `TCP-Client` |
| Socket B → Port | `18899` | `18899`, or your integration's selected port |
| Socket B → Server IP Address | `www.myheatpump.com` | HA host's LAN IPv4 address |

Example: for HA at `http://192.168.1.50:8123`, enter **192.168.1.50** as the server and **18899** as the port. Do not enter a URL, `8123`, or `0.0.0.0` in the server field. The module initiates the TCP connection; HA listens.

For an existing working cloud setup, normally only the server address changes. Preserve Wi-Fi, Socket A and serial settings. Do not copy the screenshot's serial baud rate to a different controller.

**Manual p. 8: the screenshot shows the cloud destination `www.myheatpump.com`. For local operation, enter your HA host's IP in that field instead.**

![Trans Setting and Socket B configuration from the ES manual](images/socket-b.png)

Select **Restart** after saving (manual p. 8):

![Restart button on the Save Success screen](images/restart.png)

**Do not factory-reset a working module merely to change the server.** The manual states that Reset erases its configuration (pp. 3–4). The web page's Restart applies settings without a factory reset. This procedure does not require restarting the whole heat pump.

## First-time Wi-Fi setup only

Skip this section if the module is already on your home network.

1. Join the module's **USR-W600** access point if available. The manual recommends disabling phone mobile data during setup.
2. Open `http://10.10.100.254`, using `admin` / `admin` if the credentials are still at their defaults.
3. Select **English → WiFi Setting → WiFi Work Mode → STA mode**.
4. Use **Search** to select your home **2.4 GHz** SSID, then **OK**. The manual says 5 GHz is unsupported.
5. Enter **STA Password**, save, and retain **DHCP = Enable** as shown in the guide.
6. Before the final restart, configure Socket B using the table above and verify **Network Setting → Mode = Transparent**. Serial settings must match the controller; the guide does not establish a universal baud rate for every model.
7. Select **Save → Restart**. Rejoin your home network and find the module's new IP in the router. Its setup access point may disappear in STA mode.

If the access point is missing, first look for the module on your router. Holding physical Reset for 10 seconds is the manual's factory-reset procedure, with loss of configuration, not a normal redirection step.

**WiFi Setting → STA mode → Search**, manual p. 6:

![Select STA mode and search for the home Wi-Fi network](images/wifi-sta.png)

**STA Password → Save**, manual p. 7. Enter your own Wi-Fi password:

![Home Wi-Fi SSID, password and Save fields](images/wifi-password.png)

## Verify and troubleshoot

- In HA, check **Connected clients**, increasing **Frames received / Short frames received / Long frames received**, and a current **Last frame at** timestamp. Compare incoming water temperatures with the controller display.
- In this public alpha, DHW writes are disabled. Command-channel diagnostics `fresh_verified = false` and `verified_packet_age_seconds = null` do not indicate failed telemetry.
- The controller's **Connection to the router** confirms its router connection only. **Connection to the server** is a separate indicator, not proof of HA reception. Use HA's incoming frame counters to verify local operation.
- Values remain available after disconnects in this alpha. A visible old temperature does not prove the connection is live.
- No connection: check HA setup, the destination IP/port, Save/Restart, firewall/VLAN access and container port exposure.
- Connected but no frames: check the module/controller connection and original serial settings; the protocol may be incompatible.
- Cannot open `10.10.100.254`: this is the setup access-point address; use the router-assigned IP when on the home LAN.
- HA bind error: resolve another listener using the port, or select another free port on both sides.

The controller screenshot (manual p. 9) distinguishes **Connection to the router** from **Connection to the server**. This shows a router connection, not proof of HA reception:

![Router and server connection indicators on the ES controller](images/router-status.png)

## Restore cloud access

Restore the saved Socket B settings and select **Save → Restart**. The guide uses `TCP-Client`, port `18899`, server `www.myheatpump.com`; restore your own original server if different. Verify new data on the portal.

Redirecting Socket B stops sending its stream to the vendor cloud. Installer access, cloud history and cloud error notifications may stop updating. This integration neither relays data to the cloud nor replaces those notifications. Restoring the cloud destination stops this stream reaching HA.

Local operation needs no cloud account, MAC registration or myheatpump.com credentials. The account/portal instructions on pages 9–14 of the original manual are not local integration setup steps.

Images are excerpts from pages 6–9 of the ES manual, with screen contents unchanged. Original illustration rights remain with their respective owners; the project's MIT code license does not apply to these images. [Image provenance](images/README.md).
