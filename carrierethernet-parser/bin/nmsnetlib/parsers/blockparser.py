from nmsnetlib.models.netobjects.netobjects import _vlan, _interface_local, _interface_remote, _interface_loopback, \
                                                   _interface_ip, _interface_remote, _switchport, _nameserver, \
                                                   _ntpserver, _syslogserver, _tacacs, _tacacsserver, _vcircuit, \
                                                   _vswitch, _lldpneighbor, _logicalring, _virtualring, _lagport, \
                                                   _subport, _tagged_vlan, _service
from nmsnetlib.models.models import BaseModel
import logging


### logger = logging.getLogger(__name__)
### #logger.setLevel(logging.DEBUG)
### logger.setLevel(logging.CRITICAL)
### screenformatter = logging.Formatter('%(asctime)s - %(name)s [%(lineno)d] - %(levelname)s - %(message)s')
### logprinter = logging.StreamHandler()
### logprinter.setFormatter(screenformatter)
### logger.addHandler(logprinter)
### 

class Parser(object):
    DEBUG = False

    def __init__(self, **kwargs):
        Parser.DEBUG = kwargs.get('debug', False)
        #if Parser.DEBUG:
        #    logger.setLevel(logging.DEBUG)

        self.logger = logging.getLogger(__name__)

        self.configfile = kwargs.get('configfile', "")
        self.model = kwargs.get('model', BaseModel())

    def json(self, allownull=False):
        return self.model.json(allownull)

    def parse(self):
        pass

    def mixrange(self, s):
        """
        Expands mixed ranges into single numbers.
        Ex. mixrange('1-3,6,8-10') => [1, 2, 3, 6, 8, 9, 10]
            8/7-8/20 => [8/7, 8/8, 8/9, ..., 8/20 ]

        TODO: check for 8700 where you can have 8/7 for example
        """
        #print("HOSTNAME: {}".format(self.model.host.hostname))
        #print("S = {}".format(s))
        r = []
        for i in s.split(','):
            if '-' not in i or "." in i:
                #r.append(int(i))
                r.append(i)
            else:
                # case of 8-10
                if '/' not in i:
                    l,h = map(int, i.split('-'))
                    r += range(l,h+1)
                # case of 1/1-1/20 => 1/1,1/2,1/3...1/20
                else:
                    l,h = i.split('-')
                    l1,h1 = l.split('/')
                    l2,h2 = h.split('/')
                    if (l1 == l2):
                        r += [ "{}/{}".format(l1,y) for y in range(int(h1), int(h2)+1) ]
        #print('r = {}'.format(r))
        return r        





class BlockParser(Parser):

    #DEBUG = False  ## add extra verbose details

    """
    Base class for parsing Carrier Ethernet Devices where config is grouped in blocks with clear
    start and end delimiters per block
    """
    def __init__(self, hostname=None, configfile="", keepemptyblocks=False, model=None, debug=False):
        super(BlockParser, self).__init__( **{ 'configfile': configfile, 'model': model, 'debug': debug })

        #def __init__(self, hostname=None, configfile="", keepemptyblocks=False, model=None, debug=False):
        #BlockParser.DEBUG = debug
        #if debug:
        #    logger.setLevel(logging.DEBUG)

        #self.configfile = configfile # path to the configfile that will be parsed
        self.keepemptyblocks = keepemptyblocks  # store empty config blocks

        #self.model = model or BaseModel()
        self.model.host.hostname = hostname
        
        self.pdef = None # pdef = parser definition
        self.preprocessor = True # enable or disable the preprocessor
        self.dynamicBlocks = True  # enable usage of dynamic blocks
        self.stickyDynamicBlocks = False # a sticky dynamic block assumes that a dynamic block is started and will be ended by a reBlockStart
                                         # all single lines are added to the dynamic block name that was found earlier
                                         # this is used for Cisco for example where there are no block names inside the config


        # configuration file details
        # if you use ?P<BLOCKNAME> anywhere then this will be used as the name for a block
        self.reConfigStart = None  ## compiled regex, how to recognize the start of a config file
        self.reConfigEnd = None  ## compiled regex, how to recognize the end of a config file
        self.reBlockStart = None  ## compiled regex, how to recognize the start of a new block
        self.reBlockName = None ## if defined then this will be recognized as the name of the block
        self.reBlockEnd = None ## compiled regex, how to recognize the end of a new block
        self.BlockEndRepeat = 0 ## minimum number of times the BlockEnd regex should be seen before it ends
        self.reIgnoreLine = None ## compiled regex, these lines will be ignored
        self.parseSingleLine = False ## if enabled then also parse lines outside blocks


    def __str__(self):
        return "{} <{}>".format(self.__class__.__name__, self.model.host.hostname)


    def parse(self):
        """
        Start parsing the configuration.
        This requires a configfile, throw error if the config file is not known
        Raises:
            - ValueError (no config file set)
        The purpose of the parser is to fill in the data model while parsing,
        the data model is the representation of a device.
        """
        if not self.configfile:
            raise ValueError("Unable to parse, there is no config file set.")

        #self._config = {}
        for block in self._blockreader():
            #self.config[block['block']] = self._parse_block(block)
            self._parse_block_generic(block)
            #logger.debug("BLOCK FOUND - {}:\n{}\n\n".format(block['blockname'], block['config']))

        self._link_references()



    def _link_references(self):
        """
        Function that will be executed after parsing has finished and can be used to make 
        links to objects.
        For example if you have a list of vlans + port memeberships and a list of ports
        then you can link the port memberships to the port object references.

        This function should be overridden in the device specific parsers.
        See the SAOSpoarser as example
        """
        pass


    def _parse_block_generic(self, block):
        blockname = block['blockname']
        blockconfig = block['config']

        ## TODO: this is for testing only, remove
        #if blockname == "LLDP":
        #    lines = filter(bool, (line.strip() for line in blockconfig))
        #    print(lines)
        #    parser = docutils.parsers.rst.tableparser.GridTableParser()
        #    print parser.parse(docutils.statemachine.StringList(list(lines)))
        #    return

        _def = self.pdef.get(blockname, None)
        if _def is None:
            self.logger.debug("There is no parser definition found for block '{}'".format(blockname))
            return

        self.logger.debug("Start parsing block '{}' with config: {}".format(blockname, blockconfig))

        # loop over each config line inside a block and extract variables
        # the variables are mapped to the model based on the mapper config
        for line in blockconfig[:]:
            self.logger.debug("config line found: {}".format(line))

            for regex in _def['regex']:
                rex = regex['re']
                m = rex.match(line)
                if not m: 
                    self.logger.debug("skipping - regex '{}' has no match".format(regex))
                    continue

                mapper = self.pdef['mapping'].get(regex['mapper'], None)
                if not mapper: 
                    continue

                self.logger.debug("start parsing line")

                map_var = mapper['var']
                map_class = mapper.get('class', None)
                map_var_type = ""

                # the type command gives different output in Python2 + Python3
                # list:
                #   Py2: <type 'list'>
                #   PY3: <class 'list'>
                # string:
                #   PY2: <type 'str'>
                #   PY3: <class 'str'>
                # bytes:
                #   PY2: <type 'str'>
                #   PY3: <class 'bytes'>
                # function:
                #   PY2: <type 'function'>
                #   PY3: <class 'function'>
                # class:
                #   PY2: <type 'classobj'>
                #   PY3: <class 'the class name'>
                # instance:
                #   PY2: <type 'instance'>
                #   PY3: <class '__main__.A'>
                try:
                    # get the type of the map_var parameter iin the model,
                    # this can be a list or a function or a class
                    if isinstance(eval(map_var), list):
                        map_var_type = "list"
                    elif "'function'" in str(type(eval(map_var))):
                        map_var_type = "function"
                    elif hasattr(eval(map_var), "update_parameters"):
                        map_var_type = "class"
                    else:
                        map_var_type = "-UNKNOWN-"
                    #map_var_type = str(type(eval(map_var)))
                    self.logger.debug("INSTANCE CHECK: map_var={} map_var_type={}".format(map_var, map_var_type))
                    #self.logger.debug(isinstance(eval(map_var), map_var))
                except:
                    # we got an error but check if the model was defined 
                    # as a function
                    #self.logger.debug("map_var={} map_var_type={}".format(map_var, map_var_type))
                    self.logger.error("we got an error here!")
                    if map_var == 'function' and mapper.get('function', False):
                        map_var_type = 'function'

                map_index = mapper.get('index', None)
                map_index_ref = mapper.get('indexref', None)
                #map_key = mapper['key']

                self.logger.debug("map_class={}, map_var={}, map_var_type={}, map_index={}".format(map_class, map_var, map_var_type, map_index))

                # if the variable is a Class:
                #   execute the update_parameters() function of that class
                if map_var_type == "class":
                    self.logger.debug("PARSE AS A CLASS")
                    self.logger.debug("updating class parameters: {}".format(m.groupdict()))
                    getattr(eval(map_var), 'update_parameters')(**m.groupdict())
                # if the variable is a List:
                #   'index' is set: retrieve the object if exists and update it,
                #                   otherwise create it
                #   'index' not set: add new instances of the class stored in 'class'
                elif map_var_type == "list":
                    self.logger.debug("PARSE AS A LIST")
                    l = eval(map_var)
                    obj = None
                    # find FIRST existing object matching the index
                    if map_index:
                        obj = next(iter(list(filter(lambda x: str(x) == map_index, l))), None)
                    # find FIRST existing object based on reference to the index, reference should be in groupdict()
                    if map_index_ref:
                        idx = m.groupdict().get(map_index_ref, None)
                        if idx: obj = next(iter(list(filter(lambda x: str(x) == idx, l))), None)
                    # create the new class
                    if obj is None:
                        newclass = globals()[map_class]
                        l.append(newclass(**m.groupdict()))
                        self.logger.debug("create new class: '{}' with parameters:{}".format(newclass, m.groupdict()))
                    # or update an existing object
                    else:
                        self.logger.debug("object={}".format(obj))
                        obj.update_parameters(**m.groupdict())
                # if the variable is a function then execute the function
                elif map_var_type == "function":
                    self.logger.debug("PARSE AS A FUNCTION")
                    try:
                        eval(mapper.get('function'))(**m.groupdict())
                    except:
                        print("ERROR occurred in _parse_block_generic() line 215")




    def _blockreader(self):
        '''
        Reads a config file block by block and returns the name and config of each block.
        Return: { 'blockname': "", 'config': [] }
        '''
        # regular expressions
        #reConfigStart = re.compile("config$")
        #reBlockStart = re.compile("# +(?P<BLOCK>[A-Z0-9 \-]+) *$")
        #reBlockStart = re.compile("# +(?P<BLOCK>[A-Z].+)$")
        #reBlockEnd = re.compile("#$")

        #configs = [ f for f in listdir(dir) if "ers" in f ]
        #for config in configs:
        block = self._init_empty_block()
        dynamic_blocks = []
        sticky_dynamic_block = None
        config_started = False
        inside_block = False
        blockend_count = 0
        linecount = 0 # total number of lines processed
        previous_block = ''  # keep track of the previous blockname

        # config starts immediately if there is no regex known
        if self.reConfigStart is None:
            config_started = True

        for line in open(self.configfile, 'r'):
            linecount += 1            
            # remove EOL
            line = line.replace("\r","")
            line = line.replace("\n","")

            #if linecount > 100:
            #    sys.exit(0)

            # see if this line is the end of a new block
            blockEndFound = self.reBlockEnd.match(line) if self.reBlockEnd else False

            # if we're not yet inside a block then
            # check if a line belongs to a dynamic block and store in dynamic_blocks[] to be yielded afterwards
            if (not inside_block) and self.dynamicBlocks:
                if blockEndFound:
                    sticky_dynamic_block = None
                rc = self._parse_dynamic_block(line, dynamic_blocks, sticky_dynamic_block)
                if rc:
                    sticky_dynamic_block = rc

            #if not inside_block and self.dynamicBlocks:
            #    dynamicblock_found = False
            #    for rex in self.pdef['dynamic_blocks']:
            #        m = rex.match(line)
            #        if m:
            #            dynamicblock_found = True
            #            block_name = m.groupdict().get('DYNAMICBLOCKNAME', None)
            #            block_config = m.groupdict().get('CONFIG', None)
            #            if block_name and block_config:
            #                dynblock = next(iter(list(filter(lambda x: x['blockname'] == block_name, dynamic_blocks))), None)
            #                if dynblock:
            #                    dynblock['config'].append(block_config)
            #                else:
            #                    dynamic_blocks.append(self._init_empty_block(blockname=block_name, config=[ block_config ]))
            #            break
            #    if dynamicblock_found: 
            #        continue

            # skip all other lines until the config was started
            if not config_started:
                config_started = self._parse_config_start(line)
                continue

            # see if this line is the start of a new block
            blockStartFound = self.reBlockStart.match(line) if self.reBlockStart else False            

            # if a start of a new block is found and we're not yet inside a block then initalize a new one
            if blockStartFound and (not inside_block):
                #print("> line: {}".format(line))
                #print("> block: {}".format(block))
                
                ## TODO: if a the previous block is still not yielded then do it now and create a new block
                #if inside_block and block['blockname'] and (len(block['config']) > 0) or self.keepemptyblocks:
                #    logger.debug("Block '{}' has ended ({})".format(block['blockname'], line))
                #    yield block
                inside_block = True
                d = blockStartFound.groupdict()
                blockname = d.get('BLOCKNAME', None)
                d.pop('BLOCKNAME', None)
                block = BlockParser._init_empty_block(bname=blockname)
                #block['blockname'] = blockStartFound.groupdict().get('BLOCKNAME', None)
                # get the blockname from the blockStartLine if it exists
                # reset the line counter
                # linecount = 0
                self.logger.debug("The start of new block was found ({})".format(line))
                # ignore the line if there are no other regex matches found
                if not d.keys():
                    continue
                blockStartFound = None

            # keep on adding lines to the block until end of block is seen,
            # return the block if it's not empty or unless emptyBlocks is set True

            ## # see if this line is the end of a new block
            ## blockEndFound = self.reBlockEnd.match(line) if self.reBlockEnd else False

            ## TODO: in case there is no BlockEND defined then the last block could be ignored
            if inside_block and (blockStartFound or blockEndFound):
                if blockEndFound:
                    # check if we expect multiple BlockEnd lines
                    blockend_count += 1
                    if (blockend_count < self.BlockEndRepeat):
                        self.logger.debug("Block end was found but we expect it to occur {} times.".format(self.BlockEndRepeat))
                    else:
                        inside_block = False
                    continue

                if BlockParser.DEBUG:
                    print(">> line: {}".format(line))
                    print(">> inside_block: {}".format(inside_block))
                    print(">> blockStartFound: {}".format(blockStartFound))
                    print(">> blockEndFound: {}".format(blockEndFound))
                    print(">> block: {}".format(block))
                    print(">> previous_block: {}".format(previous_block))

                # return the block if it was ended
                #print("blockname = {}".format(block['blockname']))
                #print("previous_block = {}".format(previous_block))
                #if blockEndFound or (blockStartFound and len(block['config']) > 0):

                if (len(block['config']) > 0) or self.keepemptyblocks:
                    self.logger.debug("Block '{}' has ended ({})".format(block['blockname'], block['config']))
                    yield block
                else:
                    self.logger.debug("Empty block '{}', skipping it.".format(block['blockname']))

                self.logger.debug("New block found")
                previous_block = block['blockname']
                #print("+++++++++++++++++++++++ BEFORE: {}".format(block))
                block = self._init_empty_block()
                #print("+++++++++++++++++++++++ AFTER: {}".format(block))
                blockend_count = 0
                inside_block = True
                


                #inside_block = False
                #previous_block = None

                #print("***> {}".format(line))

                    #continue

            
            # otherwise store the line in the config
            if inside_block:

                # if the blockname is not yet known then see if we can find
                if (not block["blockname"]) and (self.reBlockName is not None):
                    #print("-> {}".format(line))
                    m = self.reBlockName.match(line)
                    if m:
                        d = m.groupdict()
                        if d.get('BLOCKNAME', None):
                            #previous_block = block['blockname']
                            block['blockname'] = d.get('BLOCKNAME')
                            self.logger.debug("Block name found: {}".format(block['blockname']))
                        d.pop('BLOCKNAME')
                        if not d.keys():
                            continue

                # go to next line if there are no further parameters in the blockstartfound
                if blockStartFound:
                    d = blockStartFound.groupdict()
                    blockname = d.get('BLOCKNAME', None)
                    d.pop('BLOCKNAME', None)
                    if not d.keys():
                        blockStartFound = None
                        continue

                # ignore lines for parsing
                if self.reIgnoreLine is not None and self.reIgnoreLine.match(line):
                    self.logger.debug("Line matches the 'ignore' regex - skipping it ({})".format(line))
                    continue

                # add the configuration to the block
                #print("---> {}".format(line))
                block['config'].extend(self._parser_preprocessor(line, block['blockname']))

            # if lines outside blocks should be considered then put them in a
            # dedicated block called: _SINGLE_LINE_PARSING_
            elif self.parseSingleLine:
                block_name = '_SINGLE_LINE_PARSING_'
                block_config = self._parser_preprocessor(line, block_name)
                ## the single line could be part of a dynamic block already, check it here
                lineblock = next(iter(list(filter(lambda x: x['blockname'] == block_name, dynamic_blocks))), None)
                if lineblock:
                    lineblock['config'].extend(block_config)
                else:
                    #dynamic_blocks.append({ 'blockname': block_name, 'config': block_config })
                    dynamic_blocks.append(BlockParser._init_empty_block(bname=block_name, cfg=block_config))

            # if nothing else can be parsed then print a line debug
            else:
                self.logger.debug("*-> Line missed by the parser: {}".format(line))

        # yield the dynamic blocks
        for block in dynamic_blocks:
            if (len(block['config']) > 0) or self.keepemptyblocks:
                self.logger.debug("Dynamic Block '{}' has ended".format(block['blockname']))
                yield block


    @classmethod
    def _init_empty_block(cls, bname=None, cfg=list()):
        """
        Returns an empty block
        """
        bname = bname or None
        cfg = cfg or []
        #print("--> _init_empty_block: blockname = {}".format(bname))
        #print("--> _init_empty_block: config = {}".format(cfg))
        return dict(blockname=bname, config=cfg)


    def _parse_config_start(self, line):
        """
        Check if a line matches the start of a configuration file
        Return values
            True: a start of the config was found
            False: a start of the config was not found 
        """
        if self.reConfigStart.match(line):
            self.logger.debug("{} - The start of a config was found.".format(self.configfile))
            return True
        return False

    def _parse_dynamic_block(self, line, dynamic_blocks, sticky_dynamic_block):
        """
        Parse a line and search for a dynamic block,
        dynamic blocks are blocks not defined by the configuration
        but defined by a regex containing <DYNAMICBLOCKNAME> and <CONFIG>
        """
        ## if we're inside a sticky dynamic block then just add the line to the dynamic block
        if sticky_dynamic_block and self.stickyDynamicBlocks:
            print("Sticky block name: {}".format(sticky_dynamic_block))
            if sticky_dynamic_block in dynamic_blocks:
                dynamic_blocks[sticky_dynamic_block]['config'].append(line)
                return sticky_dynamic_block

        dynamicblock_found = False
        for rex in self.pdef['dynamic_blocks']:
            m = rex.match(line)
            if not m:
                continue

            #dynamicblock_found = True
            block_name = m.groupdict().get('DYNAMICBLOCKNAME', None)
            block_config = m.groupdict().get('CONFIG', None)
            dynamicblock_found = block_name
            self.logger.debug("Dynamic block '{}' found for line: {}".format(block_name, block_config))
            #if block_name and block_config:
            if block_name:
                dynblock = next(iter(list(filter(lambda x: x['blockname'] == block_name, dynamic_blocks))), None)
                if dynblock:
                    dynblock['config'].append(block_config)
                else:
                    dynamic_blocks.append(self._init_empty_block(bname=block_name, cfg=[ block_config ]))
            break

        return dynamicblock_found


    def _parser_preprocessor(self, line, block):
        """
        Before adding the line to the config which will be parsed,
        see if there is anything that needs to be done.
        For example expand a single line into multiple lines to simplify the parser function.
        Ex. vlan create vlan 4038-4039
         ==> change to vlan create vlan 4038
             vlan create vlan 4039
        """
        lines = [ ]
        # define the preprocessor per block to speed up the parsing
        if self.preprocessor and (block in self.pdef) and ('preprocessor' in self.pdef[block]):
            for rex in self.pdef[block]['preprocessor']['regex']:
                #print ">>>>>>>>>>>>>>>>>>>>>>>> {} ({})".format(block, line)
                m = rex.match(line)
                if m and 'MIXRANGE' in m.groupdict():
                    mixrange = self.mixrange(m.groupdict()['MIXRANGE'])
                    lines = [ line.replace(m.groupdict()['MIXRANGE'], str(mix)) for mix in mixrange ]
                    self.logger.debug("preprocessor: expand '{}' into '{}' (mixrange={})".format(line, lines, mixrange))

                elif m and 'MACTOUPPERSTRING' in m.groupdict():
                    mac = m.groupdict()['MACTOUPPERSTRING']
                    macupperstring = mac.upper().replace(":", "")
                    lines.append(line.replace(mac, macupperstring))
                    self.logger.debug("preprocessor: mac to upper from '{}' into '{}'".format(mac, macupperstring))
                elif m and 'SWITCHPORTFORMAT' in m.groupdict():
                    # replace speed/duplex and Ena/Dis
                    #sd = m.groupdict()['SWITCHPORTFORMAT']
                    startline = line
                    l = line
                    l = l.replace("0/H", "0H")
                    l = l.replace("0/F", "0F")
                    l = l.replace("Ena", "enabled")
                    l = l.replace("Dis", "disabled")
                    #print("m = {}".format(m.groupdict()["SWITCHPORTFORMAT"]))
                    if " | " in m.groupdict()["SWITCHPORTFORMAT"]:
                        a = m.groupdict()["SWITCHPORTFORMAT"]
                        a = a.replace(" | ", "/")
                        a = a.replace(" ", "")
                        l = l.replace(m.groupdict()["SWITCHPORTFORMAT"], a)
                        #print("a = {}".format(a))
                        #print("l = {}".format(l))
                    lines.append(l)                    
                    #line = l
                    self.logger.debug("preprocessor: SWITCHPORTFORMAT '{}' into '{}'".format(startline, l))
                    #print("preprocessor: SWITCHPORTFORMAT '{}' into '{}'".format(startline, l))
                elif m and 'CREATEBLOCKNAME' in m.groupdict():
                    blockname = m.groupdict()['CREATEBLOCKNAME']
                    line = "BLOCK: {} - {}".format(blockname, line)
                elif m and 'PORTNNIUNI' in m.groupdict():
                    startline = line
                    line = line.replace('Subsc', 'UNI')
                    line = line.replace('Ntwrk', 'NNI')
                    self.logger.debug("preprocessor: PORTNNIUNI '{}' into '{}'".format(startline, line))
                elif m and 'AUTONEG' in m.groupdict() and 'NAME' in m.groupdict():
                    startline = line
                    line = "! PORT_ETHERNET_CONFIGURATION: | {} | autoneg:on".format(m.groupdict()['NAME'])
                    self.logger.debug("preprocessor: AUTONEG '{}' into '{}'".format(startline, line))
                    lines.append(startline)
                    lines.append(line)
                    #print(line)
                #else:
                #    ## generate some extra config lines
                #    lines.append("! PORT_ETHERNET_CONFIGURATION: autoneg:disabled")
                #    print(lines)
                #    logger.debug("lkjlkjl")
        
        if not lines: lines.append(line)
        return lines



class LineParser(Parser):
    """
    Base class for parsing Cisco like Devices where config has to be processed line by line
    but there are groups of lines belonging to each other (ex. interface)
    """
    def __init__(self, hostname=None, configfile="", model=None, debug=False):
        super(LineParser, self).__init__( **{ 'configfile': configfile, 'model': model, 'debug': debug })

    def parse(self):
        """
        Start parsing the configuration.
        This requires a configfile, throw error if the config file is not known
        Raises:
            - ValueError (no config file set)
        The purpose of the parser is to fill in the data model while parsing,
        the data model is the representation of a device.
        """
        if not self.configfile:
            raise ValueError("Unable to parse, there is no config file set.")

        #self._config = {}
        for l in self._linereader():
            #self.config[block['block']] = self._parse_block(block)
            #self._parse_line(line)
            #logger.debug("BLOCK FOUND - {}:\n{}\n\n".format(block['blockname'], block['config']))
            self.logger.debug(">> line found: {}".format(l))

    def _linereader(self):
        """
            parses a single 
        """
        linecount = 0 # total number of lines processed

        # config starts immediately if there is no regex known
        if self.reConfigStart is None:
            config_started = True

        for line in open(self.configfile, 'r'):
            yield line.strip()


