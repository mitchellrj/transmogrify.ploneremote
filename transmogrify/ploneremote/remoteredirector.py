import urllib
import logging
from httplib import HTTPException

from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint
from collective.transmogrifier.interfaces import ISection
from collective.transmogrifier.utils import defaultMatcher

from base import PathBasedAbstractRemoteCommand 


logger = logging.getLogger('transmogrify.ploneremote.remoteredirector')

class RemoteRedirectorSection(PathBasedAbstractRemoteCommand ):
    """
    Remotely add redirection to content objects using Products.RedirectionTool
    package HTTP API (Aliases tab on content object).
    
    This blueprint depends on Products.RedirectonTool package.
    """
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __iter__(self):
        self.checkOptions()
        for item in self.previous:
            path = self.extractPath(item)
            if not path:
                yield item
                continue
            
            # check if we got any original path and it's different from current
            orig_path = item.get('_orig_path', None)
            if not orig_path or path == orig_path:
                yield item
                continue

            # RedirectionTool requires all paths to be started from slash
            if not orig_path.startswith('/'):
                orig_path = '/' + orig_path
            
            # define content item url
            url = urllib.basejoin(self.constructRemoteURL(item),
                "@@manage-aliases?redirection=%s&form.button.Add=Add" %
                urllib.quote_plus(orig_path))
            logger.info("Adding redirection from %s to %s" % (orig_path, path))
                
            try:
                f = urllib.urlopen(url)
                data = f.read()
                
                # Use Plone not found page signature to detect bad URLs
                if "Please double check the web address" in data:
                    raise RuntimeError("You need to install "
                        "Products.RedirectionTool package in order to make "
                        "ploneremote redirector blueprint work (url: %s)" % url)
            except HTTPException, e:
                # Other than HTTP 200 OK should end up here,
                # unless URL is broken in which case Plone shows
                # "Your content was not found page"
                logger.error("fail")
                msg = "Adding redirection from %s to %s failed (url: %s)" % (
                    path, orig_path, url)
                logger.log(logging.ERROR, msg, exc_info=True)
            
            yield item