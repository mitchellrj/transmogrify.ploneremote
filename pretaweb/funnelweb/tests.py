
import unittest

from zope.testing import doctest
from zope.component import provideUtility
from Products.Five import zcml
from zope.component import provideUtility
from zope.interface import classProvides, implements
from collective.transmogrifier.interfaces import ISectionBlueprint, ISection

from collective.transmogrifier.tests import setUp as baseSetUp
from collective.transmogrifier.tests import tearDown
from collective.transmogrifier.sections.tests import PrettyPrinter
from collective.transmogrifier.sections.tests import SampleSource

from pretaweb.funnelweb.webcrawler import WebCrawler
from pretaweb.funnelweb.treeserializer import TreeSerializer
from pretaweb.funnelweb.typerecognitor import TypeRecognitor
from pretaweb.funnelweb.safeportaltransforms import  SafePortalTransforms
from pretaweb.funnelweb.makeattachments import MakeAttachments
from templatefinder import TemplateFinder
from pretaweb.funnelweb.relinker import Relinker
from pretaweb.funnelweb.simplexpath import SimpleXPath
from plone.i18n.normalizer import urlnormalizer
from lxml import etree
import lxml.html
import lxml.html.soupparser
from lxml.html.clean import Cleaner
import urlparse

class HTMLSource(object):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        self.previous = previous
        def item(path, text):
            i = dict(_mimetype="text/html",_site_url="http://test.com/")
            i.update(dict(_path=key,text=value,_mimetype="text/html"))
            return i
        self.items = [item(key,value) for key,value in options.items() if key!='blueprint']
        
    def __iter__(self):
        for item in self.previous:
            yield item
            
        for item in self.items:
            yield item

class HTMLBacklinkSource(HTMLSource):
    classProvides(ISectionBlueprint)
    implements(ISection)
    
    def __init__(self, transmogrifier, name, options, previous):
        HTMLSource.__init__(self, transmogrifier, name, options, previous)
        pathtoitem = {}
        for item in self.items:
            pathtoitem[item['_site_url']+item['_path']] = item
        for item in self.items:
            parser = lxml.html.soupparser.fromstring(item['text'])
            for element, attribute, rawlink, pos in parser.iterlinks():
                t = urlparse.urlparse(rawlink)
                fragment = t[-1]
                t = t[:-1] + ('',)
                rawlink = urlparse.urlunparse(t)
                base = item['_site_url']+item['_path']
                link = urlparse.urljoin(base, rawlink)
                linked = pathtoitem.get(link)
                if linked:
                    linked.setdefault('_backlinks',[]).append((base,element.text_content()))


class MockPortalTransforms(object):
    def __call__(self, transform, data):
        return 'Transformed %i using the %s transform' % (len(data), transform)
    def convertToData(self, target, data, mimetype=None):
        html='<img src="image01.jpg"><img src="image02.jpg">'
        class dummyfile:
            def __init__(self, text):
                self.text = text
            def __str__(self):
                return self.text+html
            def getSubObjects(self):
                return {'image01.jpg':data,'image02.jog':data}
        if mimetype is not None:
            return dummyfile( 'Transformed %i from %s to %s' % (
                len(data), mimetype, target) )
        else:
            return dummyfile('Transformed %r to %s' % (data, target) )
    def convertTo(self, target, data, mimetype=None):
        return self.convertToData(target,data,mimetype)



def setUp(test):
    baseSetUp(test)
        
    from collective.transmogrifier.transmogrifier import Transmogrifier
    test.globs['transmogrifier'] = Transmogrifier(test.globs['plone'])
    
    import zope.component
    import collective.transmogrifier.sections
    zcml.load_config('meta.zcml', zope.app.component)
    zcml.load_config('configure.zcml', collective.transmogrifier.sections)
    
    test.globs['plone'].portal_transforms = MockPortalTransforms()
    
    provideUtility(PrettyPrinter,
        name=u'collective.transmogrifier.sections.tests.pprinter')
    provideUtility(WebCrawler,
        name=u'pretaweb.funnelweb.webcrawler')
    provideUtility(TreeSerializer,
        name=u'pretaweb.funnelweb.treeserializer')
    provideUtility(TypeRecognitor,
        name=u'pretaweb.funnelweb.typerecognitor')
    provideUtility(TemplateFinder,
        name=u'pretaweb.funnelweb.templatefinder')
    provideUtility(urlnormalizer)
    provideUtility(Relinker,
        name=u'pretaweb.funnelweb.relinker')
    provideUtility(SimpleXPath,
        name=u'pretaweb.funnelweb.simplexpath')
    provideUtility(SafePortalTransforms,
        name=u'pretaweb.funnelweb.safeportaltransforms')
    from backlinkstitle import BacklinksTitle
    provideUtility(BacklinksTitle,
        name=u'pretaweb.funnelweb.backlinkstitle')
    from isindex import IsIndex
    provideUtility(IsIndex,
        name=u'pretaweb.funnelweb.isindex')
    from pathmover import PathMover
    provideUtility(PathMover,
        name=u'pretaweb.funnelweb.pathmover')
    from safeatschemaupdater import SafeATSchemaUpdaterSection
    provideUtility(SafeATSchemaUpdaterSection,
        name=u'pretaweb.funnelweb.safeatschemaupdater')
    from constructor import SafeConstructorSection
    provideUtility(SafeConstructorSection,
        name=u'pretaweb.funnelweb.constructor')
    from makeattachments import MakeAttachments
    provideUtility(MakeAttachments,
        name=u'pretaweb.funnelweb.makeattachments')
    from debugsection import DebugSection
    provideUtility(DebugSection,
        name=u'pretaweb.funnelweb.debugsection')
    from staticcreator import StaticCreator
    provideUtility(StaticCreator,
        name=u'pretaweb.funnelweb.staticcreator')

    provideUtility(HTMLSource,
        name=u'pretaweb.funnelweb.test.htmlsource')
    provideUtility(HTMLBacklinkSource,
        name=u'pretaweb.funnelweb.test.htmlbacklinksource')


def SafeATSchemaUpdaterSetUp(test):
    setUp(test)

    from Products.Archetypes.interfaces import IBaseObject
    class MockPortal(object):
        implements(IBaseObject)
        
        def unrestrictedTraverse(self, path, default):
            return self

        _file_value = None
        _file_filename = None
        _file_mimetype = None
        _file_field = None

        def set(self, name, value, **arguments):
            self._file_field = name
            self._file_value = value
            if 'mimetype' in arguments:
                self._file_mimetype = arguments['mimetype']
            if 'filename' in arguments:
                self._file_filename = arguments['filename']

        def get(self, name):
            return self._file_value
        
        def checkCreationFlag(self):
            pass

        def unmarkCreationFlag(self):
            pass

        def getField(self, name):
            return self

    test.globs['plone'] = MockPortal()
    test.globs['transmogrifier'].context = test.globs['plone']

    class SafeATSchemaUpdaterSectionSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)

        def __init__(self, *args, **kw):
            super(SafeATSchemaUpdaterSectionSource, self).__init__(*args, **kw)
            self.sample = (
                {'_path': '/dummy',
                 'file': 'image content',
                 'file.filename': 'image.jpg',
                 'file.mimetype': 'image/jpeg',},
            )
    provideUtility(SafeATSchemaUpdaterSectionSource,
        name=u'pretaweb.funnelweb.tests.safeatschemaupdatersource')

def MakeAttachmentsSetUp(test):
    setUp(test)

    class MakeAttachmentsSource(SampleSource):
        classProvides(ISectionBlueprint)
        implements(ISection)

        def __init__(self, *args, **kw):
            super(MakeAttachmentsSource, self).__init__(*args, **kw)
            self.sample = (
                {'_site_url': 'http://www.test.com',
                 '_path': '/item1',},
                {'_site_url': 'http://www.test.com',
                 '_path': '/subitem1',
                 '_backlinks': [('http://www.test.com/subitem2', '')],
                 'title': 'subitem1 title',
                 'decription': 'test if condition is working',
                 '_type': 'Document'},
                {'_site_url': 'http://www.test.com',
                 '_path': '/subitem2',
                 '_backlinks': [('http://www.test.com/subitem1', '')],
                 'title': 'subitem2 title',
                 'image': 'subitem2 image content',
                 '_type': 'Image'},
            )
    provideUtility(MakeAttachmentsSource,
        name=u'pretaweb.funnelweb.tests.makeattachments')
    provideUtility(MakeAttachments,
        name=u'pretaweb.funnelweb.makeattachments')


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('webcrawler.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('treeserializer.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('typerecognitor.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('templatefinder.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('relinker.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('pathmover.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('simplexpath.txt', setUp=setUp, tearDown=tearDown),
        doctest.DocFileSuite('safeatschemaupdater.txt',
                setUp=SafeATSchemaUpdaterSetUp,
                tearDown=tearDown),
        doctest.DocFileSuite('makeattachments.txt',
                setUp=MakeAttachmentsSetUp,
                tearDown=tearDown),
        doctest.DocFileSuite('isindex.txt',
                setUp=MakeAttachmentsSetUp,
                tearDown=tearDown),
        doctest.DocFileSuite('safeportaltransforms.txt',
                setUp=MakeAttachmentsSetUp,
                tearDown=tearDown),
    ))

