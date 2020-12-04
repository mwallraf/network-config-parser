import re

## Ciena ERS definition
definition = {
            'LOG CONFIGURATION': {
                    'regex': [ 
                        { 'mapper': 'HOST', 're': re.compile("log transferFile 1 filename (?P<hostname>.*)(?:-CPU)") }
                    ],
            },
            'LICENSE CONFIGURATION': {
                    'regex': [ 
                        { 'mapper': 'HOST', 're': re.compile("pbt-base-mac (?P<chassisid>[A-F0-9]{12})") }
                    ],
                    'preprocessor': {
                        'regex': [
                            re.compile("pbt-base-mac (?P<MACTOUPPERSTRING>[a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2})"),
                        ]
                    }
            },
            'NTP CONFIGURATION': {
                    'regex': [ 
                        { 'mapper': 'NTPSERVER', 're': re.compile("ntp server create (?P<ip>.+)") }
                    ],
            },
            'PORT CONFIGURATION - PHASE II': {
                    'regex': [ 
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) default-vlan-id *(?P<defaultvlanid>[0-9]+)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) speed (?P<adminspeedduplex>[0-9]+)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) auto-negotiate (?P<autoneg>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) name \"(?P<description>.*)\"") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) state (?P<adminstate>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) stg 1 stp (?P<stp>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) untagged-frames-discard (?P<untaggedframesdiscard>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) tdp (?P<tdp>.*)") },
                        { 'mapper': 'SWITCHPORT', 're': re.compile("ethernet (?P<name>[^ ]+) cp-limit (?P<stormcontrol>[^ ]+) multicast-limit (?P<multicastlimit>[0-9]+) broadcast-limit (?P<broadcastlimit>[0-9]+)") },
                    ],
            },
            ## special config, when single line parsing is enabled this block is created automatically
            '_SINGLE_LINE_PARSING_': {
                    'regex': [ 
                    ],
                    'preprocessor': {
                        'regex': [
                        ]
                    }
            },
            ## the mapping maps the above regular expressions to the model
            'mapping': {
                'HOST': { 'var': 'self.model.host' },
                'NTPSERVER': { 'var': 'self.model.ntpservers', 'class': '_nameserver' },
                'SWITCHPORT': { 'var': 'self.model.switchports', 'class': '_switchport', 'indexref': 'name' },
            },
            ## regexes matches here will create a dynamic block automatically
            'dynamic_blocks': [
            ],
        }
