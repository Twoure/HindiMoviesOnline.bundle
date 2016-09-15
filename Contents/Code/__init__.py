import bookmarks
import messages
from DumbTools import DumbKeyboard

TITLE = 'Hindi Movies Online'
PREFIX = '/video/hindimoviesonline'
BASE_URL = 'http://hindimoviesonline.cc'

ICON = 'icon-default.png'
ART = 'art-default.jpg'
BOOKMARK_ADD_ICON = 'icon-add-bookmark.png'
BOOKMARK_REMOVE_ICON = 'icon-remove-bookmark.png'
FALLBACK = 'http://i.imgur.com/75YO83o.jpg'
OFFLINE = BASE_URL + '/wp-content/themes/awaken/images/thumbnail-default.jpg'

BM = bookmarks.Bookmark(PREFIX, TITLE, BOOKMARK_ADD_ICON, BOOKMARK_REMOVE_ICON)
MC = messages.NewMessageContainer(PREFIX, TITLE)

####################################################################################################
def Start():

    ObjectContainer.title1 = TITLE

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

    InputDirectoryObject.art = R(ART)

    VideoClipObject.art = R(ART)

    Log.Debug('*' * 80)
    Log.Debug('* Platform.OS            = %s' %Platform.OS)
    Log.Debug('* Platform.OSVersion     = %s' %Platform.OSVersion)
    Log.Debug('* Platform.ServerVersion = %s' %Platform.ServerVersion)
    Log.Debug('*' * 80)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'

####################################################################################################
@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()

    oc.add(DirectoryObject(
        key=Callback(DirectoryList, title='Latest', href='/latest-bollywood-movies-online/'),
        title='Latest', thumb=R('icon-calendar.png')
        ))
    oc.add(DirectoryObject(
        key=Callback(SideList, title='New Releases', href='/wp-content/uploads/new.html'),
        title='New Releases', thumb=R('icon-ticket.png')
        ))
    oc.add(DirectoryObject(
        key=Callback(BookmarksMain), title='My Bookmarks', thumb=R('icon-bookmarks.png')
        ))
    if Client.Product in DumbKeyboard.clients:
        DumbKeyboard(PREFIX, oc, Search, dktitle='Search', dkthumb=R('icon-search.png'))
    else:
        oc.add(InputDirectoryObject(
            key=Callback(Search), title='Search', prompt='Search for...', thumb=R('icon-search.png')
            ))

    return oc

####################################################################################################
@route(PREFIX + '/bookmarksmain')
def BookmarksMain():
    bm = Dict['Bookmarks']
    if not bm:
        return MC.message_container('Bookmarks', 'Bookmarks list Empty')

    oc = ObjectContainer(title2='My Bookmarks', no_cache=True)

    for key in sorted(bm.keys()):
        if len(bm[key]) == 0:
            del Dict['Bookmarks'][key]
            Dict.Save()
        elif 1 >= len(bm.keys()) > 0:
            return BookmarksSub(category=key)

    if len(oc) > 0:
        return oc

    return MC.message_container('Bookmarks', 'Bookmark list Empty')

####################################################################################################
@route(PREFIX + '/bookmarkssub')
def BookmarksSub(category):
    bm = Dict['Bookmarks']
    if not category in bm.keys():
        return MC.message_container('Error',
            '%s Bookmarks list is dirty, or no %s Bookmark list exist.' %(category, category))

    oc = ObjectContainer(title2='My Bookmarks / %s' %category, no_cache=True)

    for bookmark in sorted(bm[category], key=lambda k: k['title']):
        title = bookmark['title']
        thumb = bookmark['thumb']
        url = bookmark['url']

        oc.add(DirectoryObject(
            key=Callback(VideoPage, title=title, thumb=thumb, url=url),
            title=title, thumb=Resource.ContentsOfURLWithFallback([thumb, FALLBACK])
            ))

    if len(oc) != 0:
        return oc

    return MC.message_container('Bookmarks', '%s Bookmarks list Empty' %category)

####################################################################################################
@route(PREFIX + '/directorylist')
def DirectoryList(title, href):
    url = href if href.startswith('http') else BASE_URL + href
    html = HTML.ElementFromURL(url)

    oc = ObjectContainer(title2=title)

    for node in html.xpath('//article'):
        anode = node.xpath('.//a')
        nhref = anode[0].get('href') if anode else None
        url = nhref if nhref.startswith('http') else (BASE_URL + nhref if nhref else None)
        ntitle = anode[0].get('title') if anode else None
        thumb = node.xpath('.//img/@src')
        thumb = thumb[0] if thumb else FALLBACK

        if nhref and ntitle and (thumb != OFFLINE):
            oc.add(DirectoryObject(
                key=Callback(VideoPage, title=ntitle, thumb=thumb, url=url),
                title=ntitle, thumb=Resource.ContentsOfURLWithFallback([thumb, FALLBACK])
                ))

    np = html.xpath('//link[@rel="next"]/@href')
    if np and (len(oc) != 0):
        lp = 1
        for p in html.xpath('//a[@class="page-numbers"][@href]'):
            if p.text == '1':
                continue

            n = int(p.get('href').rsplit('/', 2)[1])
            if n > lp:
                lp = n

        oc.add(NextPageObject(
            key=Callback(DirectoryList, title=title, href=np[0]),
            title='Next %s of %i >>' %(np[0].rsplit('/', 2)[1], lp)
            ))

    if len(oc) != 0:
        return oc

    return MC.message_container('Warning', 'Media List Empty')

####################################################################################################
@route(PREFIX + '/sidelist')
def SideList(title, href):
    url = href if href.startswith('http') else BASE_URL + href
    html = HTML.ElementFromURL(url)

    oc = ObjectContainer(title2=title)

    ul = html.xpath('//h3[text()="New Releases"]/following-sibling::ul')
    for node in ul[0].xpath('.//a'):
        nhref = node.get('href')
        url = nhref if nhref.startswith('http') else (BASE_URL + nhref if nhref else None)
        ntitle = node.text

        if nhref and ntitle:
            oc.add(DirectoryObject(
                key=Callback(VideoPage, title=ntitle, thumb='', url=url),
                title=ntitle, thumb=Resource.ContentsOfURLWithFallback([FALLBACK])
                ))

    if len(oc) != 0:
        return oc

    return MC.message_container('Warning', 'Media List Empty')

####################################################################################################
@route(PREFIX + '/videopage')
def VideoPage(title, thumb, url):

    url = url if url.startswith('http') else BASE_URL + url
    item_id = url.split('/')[(-2 if url.endswith('/') else -1)]
    category = "Movie"

    try:
        html = HTML.ElementFromURL(url)
    except:
        return MC.message_container('Error', 'Cannot access %s' %url)

    if not is_uss_installed():
        return MC.message_container('Error', 'UnSupportedServices.bundle Required')

    source_list = html.xpath('//iframe/@src')
    if len(source_list) == 0:
        return MC.message_container('Warning', 'No Source Video(s)')

    oc = ObjectContainer(title2=title, no_cache=True)

    cslist = list()
    for src in source_list:
        # Trick to use the UnSupportedServices URL Service for URLs within the trick_list
        trick_list = ['vidzi', 'vodlocker', 'gorillavid', 'faststream']
        test = ['uss/' + src for u in trick_list if Regex(r'(?:\.|\/)(%s)\.' %u).search(src)]
        src = test[0] if test else src

        if (URLService.ServiceIdentifierForURL(src) is not None):
            cslist.append(src)

    if len(cslist) == 0:
        return MC.message_container('Warning', 'Media has Expired')

    mtime = html.xpath('//meta[@property="article:modified_time"]/@content')
    uptime = html.xpath('//meta[@property="og:updated_time"]/@content')

    originally_available_at = uptime[0] if uptime else (mtime[0] if mtime else None)
    year = int(Datetime.ParseDate(originally_available_at).year) if originally_available_at else None
    originally_available_at = Datetime.ParseDate(originally_available_at) if originally_available_at else None

    node = html.xpath('//div/img')
    vtitle = node[0].get('alt') if node else None
    if not vtitle:
        vtitle = html.xpath('//h1[@class="single-entry-title"]/text()')[0] if html.xpath('//h1[@class="single-entry-title"]/text()') else None
    vtitle = Regex(r'^(.+?)[Ff]ull\s[Mm]ovie(?:\s[Oo]nline)?$').sub(r'\1', vtitle.strip()) if vtitle else None
    if not vtitle:
        vtitle = 'Title NA'

    thumb = thumb if thumb else ''
    vthumb = node[0].get('src') if node else thumb

    source_title = 'HindiMoviesOnline'

    for u in cslist:
        hmo_url = 'hmo:%s' %(u + '&hmo_page_url=' + url)
        host = Regex(r'https?\:\/\/([^\/]+)').search(u).group(1).replace('www.', '')
        if len(cslist) == 1:
            ntitle = vtitle if vtitle else host
        else:
            ntitle ='%s - %s' %(host, vtitle) if vtitle else host

        oc.add(MovieObject(
            source_title=source_title,
            title=ntitle,
            thumb=Resource.ContentsOfURLWithFallback([vthumb, thumb, FALLBACK]),
            originally_available_at=originally_available_at,
            year=year,
            url=hmo_url
            ))

    if len(oc) != 0:
        BM.add_remove_bookmark(vtitle, vthumb, url, item_id, category, oc)
        return oc
    elif BM.bookmark_exist(item_id, category):
        oc.header = 'Warning'
        oc.message = 'Item no longer available. Please remove from Bookmarks.'
        BM.add_remove_bookmark(vtitle, vthumb, url, item_id, category, oc)

    return MC.message_container('Warning', 'No Video Sources')

####################################################################################################
@route(PREFIX + '/search')
def Search(query=''):
    query = query.strip()
    title = 'Search for \"%s\"' %query
    href = BASE_URL + '/?s=%s' %String.Quote(query, usePlus=True)

    return DirectoryList(title, href)

####################################################################################################
def is_uss_installed():
    """Check install state of UnSupported Services"""

    identifiers = list()
    plugins_list = XML.ElementFromURL('http://127.0.0.1:32400/:/plugins', cacheTime=0)

    for plugin_el in plugins_list.xpath('//Plugin'):
        identifiers.append(plugin_el.get('identifier'))

    if 'com.plexapp.system.unsupportedservices' in identifiers:
        return True
    return False
