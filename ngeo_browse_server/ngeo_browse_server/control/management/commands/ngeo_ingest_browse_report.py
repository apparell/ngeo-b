import os
import logging
from lxml import etree
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from ngeo_browse_server.control.ingest import ingest_browse_report
from ngeo_browse_server.control.ingest.parsing import parse_browse_report
from ngeo_browse_server.config import get_ngeo_config


logger = logging.getLogger(__name__)

class LogToConsoleMixIn(object):
    """ Helper mix-in to redirect logs to the `sys.stderr` stream. """
    def set_up_logging(self, loggernames, verbosity=None, traceback=False):
        verbosity = int(verbosity)
        if verbosity is None:
            verbosity = 1
        
        if verbosity > 4:
            verbosity = 4
        elif verbosity < 0:
            verbosity = 0 
        
        VERBOSITY_TO_LEVEL = {
            0: logging.CRITICAL,
            1: logging.ERROR,
            2: logging.WARNING,
            3: logging.INFO,
            4: logging.DEBUG
        }
        level = VERBOSITY_TO_LEVEL[verbosity]
        
        # set up logging
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        for name in loggernames:
            logging.getLogger(name).addHandler(handler)
        

class Command(LogToConsoleMixIn, BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--on-error',
            dest='on_error', default="stop",
            choices=["continue", "stop"],
            help="Declare how errors shall be handled. Default is 'stop'."
        ),
        make_option('--delete-on-success', action="store_true",
            dest='delete_on_success', default=False,
            help=("If this option is set, the original browse files will be "
                  "deleted and only the optimized browse files will be kept.")
        ),
        make_option('--storage-dir',
            dest='storage_dir',
            help=("Use this option to set a path to a custom directory "
                  "entailing the browse raster files to be processed. By "
                  "default, the `storage_dir` option of the ngeo.conf will be "
                  "used.")
        ),
        make_option('--optimized-dir',
            dest='optimized_dir',
            help=("Use this option to set a path to a custom directory "
                  "to store the processed and optimized files. By default, the "
                  "`optimized_files_dir` option of the ngeo.conf will be used.")
        ),
        make_option('--create-result', action="store_true",
            dest='create_result', default=False,
            help=("Use this option to generate an XML ingestion result instead " 
                  "of the usual command line output. The result is printed on "
                  "the standard output stream.")
        )
    )
    
    args = ("<browse-report-xml-file1> [<browse-report-xml-file2>] "
            "[--on-error=<on-error>] [--delete-on-success] [--use-store-path | "
            "--path-prefix=<path-to-dir>]")
    help = ("Ingests the specified ngEO Browse Reports. All referenced browse "
            "images are optimized and saved to the configured directory as " 
            "specified in the 'ngeo.conf'. Optionally deletes the original "
            "browse raster files if they were successfully ingested.")

    def handle(self, *filenames, **kwargs):
        # parse command arguments
        verbosity = kwargs.get("verbosity", 1)
        traceback = kwargs.get("traceback", False)
        self.set_up_logging(["ngeo_browse_server"], verbosity, traceback)
        
        on_error = kwargs["on_error"]
        delete_on_success = kwargs["delete_on_success"]
        storage_dir = kwargs.get("storage_dir")
        optimized_dir = kwargs.get("optimized_dir")
        create_result = kwargs["create_result"]
        
        # check consistency
        if not len(filenames):
            raise CommandError("No input files given.")
        
        # all paths are relative to the current working directory if they are
        # not yet absolute themselves
        if storage_dir is not None:
            storage_dir = os.path.abspath(storage_dir)
            
        if optimized_dir is not None:
            optimized_dir = os.path.abspath(optimized_dir)
            
        
        # TODO: set config values here
        section = "control.ingest"
        config = get_ngeo_config()
        config.set(section, "storage_dir", storage_dir)
        config.set(section, "optimized_dir", optimized_dir)
        config.set(section, "delete_on_success", delete_on_success)
        
        # handle each file seperately
        for filename in filenames:
            try:
                # handle each browse report
                self._handle_file(filename, create_result, config)
            except Exception, e:
                # handle exceptions
                if on_error == "continue":
                    # just print the traceback and continue
                    self.print_msg("%s: %s" % (type(e).__name__, str(e)),
                                   1, error=True)
                    continue
                
                elif on_error == "stop":
                    # reraise the exception to stop the execution
                    raise
                


    def _handle_file(self, filename, create_result, config):
        logger.info("Processing input file '%s'." % filename)
        
        # parse the xml file and obtain its data structures as a 
        # parsed browse report.
        logger.info("Parsing XML file '%s'." % filename)
        document = etree.parse(filename)
        parsed_browse_report = parse_browse_report(document.getroot())
        
        # ingest the parsed browse report
        logger.info("Ingesting browse report with %d browses.")
        
        if not create_result:
            result = ingest_browse_report(parsed_browse_report,
                                          reraise_exceptions=True,
                                          config=config)
            
            logger.info("%d browses have been successfully ingested. %d "
                        "replaced, %d inserted."
                         % (result.to_be_replaced, result.actually_replaced,
                            result.actually_inserted))    
            
        else:
            result = ingest_browse_report(parsed_browse_report,
                                          reraise_exceptions=False,
                                          config=config)
            
            # print ingest result
            print(render_to_string("control/ingest_response.xml",
                                   {"result": result}))
