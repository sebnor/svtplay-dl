# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
from __future__ import absolute_import
import re
import copy
import json

from svtplay_dl.service import Service
from svtplay_dl.fetcher.hls import HLS, hlsparse
from svtplay_dl.fetcher.http import HTTP
from svtplay_dl.error import ServiceError

class Ruv(Service):
    supported_domains = ['ruv.is']

    def get(self, options):
        data = self.get_urldata()

        if self.exclude(options):
            return

        match = re.search(r'"([^"]+geo.php)"', data)
        if match:
            data = self.http.request("get", match.group(1)).content
            match = re.search(r'punktur=\(([^ ]+)\)', data)
            if match:
                janson = json.loads(match.group(1))
                options.live = checklive(janson["result"][1])
                streams = hlsparse(self.http.request("get", janson["result"][1]).text)
                for n in list(streams.keys()):
                    yield HLS(copy.copy(options), streams[n], n)
            else:
                yield ServiceError("Can't find json info")
        else:
            match = re.search(r'<source [^ ]*[ ]*src="([^"]+)" ', self.get_urldata())
            if not match:
                yield ServiceError("Can't find video info for: %s", self.url)
                return
            if match.group(1).endswith("mp4"):
                yield HTTP(copy.copy(options), match.group(1), 800)
            else:
                m3u8_url = match.group(1)
                options.live = checklive(m3u8_url)
                yield HLS(copy.copy(options), m3u8_url, 800)

def checklive(url):
    return True if re.search("live", url) else False