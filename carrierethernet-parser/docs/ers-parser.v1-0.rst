==========
ERS Parser
==========

*******
Version
*******

Current version = ``v1.0``

***************
Description
***************

Parse a folder of ERS config files and return the list of all TDI's found in each config file. Extra information related to the TDI like UNI and Ring info is also displayed.

Only TDI's are currently being reported, UNI's or Rings without TDI are not being displayed.

***************
Usage
***************

``cd /opt/SCRIPTS/TROPS/ers-parser``

``./run-ers-parser.sh``

The result will be a list of TDI in CSV format being printed to the screen. Add ``--help`` to display the commandline options. Redirect the output if you want to save to a file.

**Other examples:**

``./run-ers-parser.sh > /tmp/report.csv``


Commandline options
===================

Use ``--help`` to show all commandline options

``./run-ers-parser.sh --help``


::

    usage: ers-parser.py [-h] [-c CONFIG_DIR] [-D DELIM] [-v] [-q] [-d]

    Parse all ERS backup config files and generate a list of TDI's and the corresponding UNI + Ring information.

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG_DIR, --config-dir CONFIG_DIR
                            Dir where the ERS backup configs can be found (default
                            = /opt/configs/ERS/configs/)
      -D DELIM, --delim DELIM
                            Column delimiter used for output (default = |)
      -v, --verbose         Show extra logging info on screen (default = False)
      -q, --quiet           Quiet output, only show the summary results (default =
                            False)
      -d, --debug           Enable debug mode, logs are saved in the debug folder
                            (default = False)
    
    Current version: 1.0
    
    -- HISTORY --
    1.0 - 20170804 - initial version


***************
Sample output
***************

``./run-ers-parser.sh``

::

    # report of all TDI's found in each ERS backup configuration
    # matching UNI and RING info is also displayed
    # UNI's or RINGS for which a TDI does not exist will not be displayed
    ERS|MgmtIp|TdiId|UniAddr|TdiName|UniName|UniAdminState|UniConMode|RemoteUni|IngressCosProfileName|PriMapping|QTags|UNI_name|UNI_state|UNI_port|UNI_service_type|ring-mod-port|UNI_Mod_id|UNI_Port_id|Rin
    g_id|Ring_name|Ring_primary_port|Ring_secondary_port|Ring_state|Ring_copy_pbits
    00009-ers10-002|10.155.9.2/24|1000001|9.2.8.3|IPVPN_InternetVPN|IPVPN_InernetVPN|enable|p2p|9.2.8.4|1000M-Pir-New|0:0:0:0:0:0:0:0|||enable|8/3|tls-transparent|||||||||
    00009-ers10-002|10.155.9.2/24|1000001|9.2.8.4|IPVPN_InternetVPN|IPVPN_InernetVPN|enable|p2p|9.2.8.3|1000M-Pir-New|0:0:0:0:0:0:0:0|||enable|8/4|tls-transparent|||||||||
    00009-ers10-002|10.155.9.2/24|1000071|9.2.7.2|VT51442|ET00034243|enable|p2p|9.24.1.5|4M-Pir-New|0:0:0:0:0:0:0:0|108||enable|7/2||||||||||
    00009-ers10-002|10.155.9.2/24|1000071|9.24.1.5|VT51442|ET00034242|enable|p2p|9.2.7.2|4M-Pir-New|0:0:0:0:0:0:0:0|108||enable|||2 mod-id 3 port-id 5|3|5|2|"10131/35"|10/4|1/4|enable|disable
    00009-ers10-002|10.155.9.2/24|1000275|9.2.8.10|VT88775|ET00063282|enable|p2p|9.136.1.1|10M-Pir-New|0:0:0:0:0:0:0:0|319||enable|8/10||||||||||
    00009-ers10-002|10.155.9.2/24|1000275|9.136.1.1|VT88775|ET00063283|enable|p2p|9.2.8.10|10M-Pir-New|0:0:0:0:0:0:0:0|319||enable|||6 mod-id 8 port-id 1|8|1|6|"10132/34"|10/8|1/8|enable|disable
    00009-ers10-002|10.155.9.2/24|1000327|9.21.1.3|VT89710|ET00030815|enable|p2p|2.30.1.14|100M-Pir-New|0:0:0:0:0:0:0:0|||enable||tls-transparent|200 mod-id 1 port-id 3|1|3|200|"00009-ESU01-001"|10/1|1/1|
    enable|disable


