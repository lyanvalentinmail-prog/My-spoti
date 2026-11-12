// Openly licensed Internet Archive download source for Orpheon extension API 1.
// It never downloads Spotify audio. It only returns files whose item has an explicit
// Creative Commons/public-domain licence and whose title, artist and duration match.
(function () {
  'use strict';

  var SEARCH_URL = 'https://archive.org/advancedsearch.php';
  var METADATA_URL = 'https://archive.org/metadata/';
  var DOWNLOAD_URL = 'https://archive.org/download/';
  var MAX_STRICT_ITEMS = 8;
  var MAX_BROAD_ITEMS = 4;

  function supports(name) {
    return myspoti.features && myspoti.features.indexOf(name) >= 0;
  }

  function spanish() {
    var locale = String(myspoti.locale || 'en').toLowerCase();
    return locale === 'es' || locale.indexOf('es-') === 0;
  }

  function message(en, es) {
    return spanish() ? es : en;
  }

  function outcome(name, fields) {
    if (!supports('results')) return null;
    var result = { outcome: name };
    Object.keys(fields || {}).forEach(function (key) { result[key] = fields[key]; });
    return result;
  }

  function list(value) {
    if (value == null) return [];
    return Array.isArray(value) ? value : [value];
  }

  function first(value) {
    var values = list(value);
    return values.length ? String(values[0]) : '';
  }

  function fold(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[áàâãäå]/g, 'a')
      .replace(/[éèêë]/g, 'e')
      .replace(/[íìîï]/g, 'i')
      .replace(/[óòôõö]/g, 'o')
      .replace(/[úùûü]/g, 'u')
      .replace(/ñ/g, 'n')
      .replace(/ç/g, 'c')
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/^\s+|\s+$/g, '')
      .replace(/\s+/g, ' ');
  }

  function withoutFeaturing(value) {
    return String(value || '')
      .replace(/\s*[\[(](?:feat(?:uring)?|ft)\.?\s+[^\])]+[\])]/ig, '')
      .replace(/\s+-\s+(?:feat(?:uring)?|ft)\.?\s+.*$/ig, '');
  }

  function titleKeys(value) {
    var full = fold(value);
    var shortTitle = fold(withoutFeaturing(value));
    var keys = [];
    if (full) keys.push(full);
    if (shortTitle && shortTitle !== full) keys.push(shortTitle);
    return keys;
  }

  function intersects(left, right) {
    for (var i = 0; i < left.length; i += 1) {
      if (right.indexOf(left[i]) >= 0) return true;
    }
    return false;
  }

  function splitArtists(value) {
    var result = [];
    list(value).forEach(function (entry) {
      String(entry || '').split(/[;,]/).forEach(function (artist) {
        var key = fold(artist);
        if (key && result.indexOf(key) < 0) result.push(key);
      });
    });
    return result;
  }

  function trackArtists(track) {
    var artists = list(track.artists);
    if (!artists.length && track.artist) artists = [track.artist];
    var result = [];
    artists.forEach(function (artist) {
      var key = fold(artist);
      if (key && result.indexOf(key) < 0) result.push(key);
    });
    return result;
  }

  function artistMatches(candidate, track) {
    return intersects(splitArtists(candidate), trackArtists(track));
  }

  function candidateTitles(file) {
    var candidates = [];
    function add(value) {
      titleKeys(value).forEach(function (key) {
        if (key && candidates.indexOf(key) < 0) candidates.push(key);
      });
    }
    add(file.title);
    add(file.track);
    var name = String(file.name || '').replace(/\.[^.]+$/, '');
    name = name.replace(/^\s*(?:cd\s*)?\d+(?:[-_.]\d+)?\s*[-_. ]+\s*/i, '');
    add(name);
    var pieces = name.split(/\s+-\s+/);
    if (pieces.length > 1) add(pieces[pieces.length - 1]);
    return candidates;
  }

  function parseDuration(value) {
    if (value == null || value === '') return null;
    var text = String(value).replace(/^\s+|\s+$/g, '');
    if (/^\d+(?:\.\d+)?$/.test(text)) return Number(text) * 1000;
    if (!/^\d{1,3}:\d{1,2}(?::\d{1,2}(?:\.\d+)?)?$/.test(text)) return null;
    var parts = text.split(':').map(Number);
    var seconds = 0;
    for (var i = 0; i < parts.length; i += 1) seconds = seconds * 60 + parts[i];
    return seconds * 1000;
  }

  function durationMatches(file, track) {
    var expected = Number(track.durationMs || 0);
    if (!expected) return true;
    var actual = parseDuration(file.length != null ? file.length : file.duration);
    if (actual == null) return false;
    return actual >= expected - 5000 && actual <= expected + 15000;
  }

  function allowedLicence(value) {
    return list(value).some(function (entry) {
      var url = String(entry || '').toLowerCase().replace(/^http:/, 'https:');
      return url.indexOf('https://creativecommons.org/licenses/') === 0 ||
        url.indexOf('https://creativecommons.org/publicdomain/') === 0;
    });
  }

  function formatOf(file) {
    var format = String(file.format || '').toLowerCase();
    var name = String(file.name || '').toLowerCase();
    if (format.indexOf('flac') >= 0 || /\.flac$/.test(name)) return 'flac';
    if (format.indexOf('mp3') >= 0 || /\.mp3$/.test(name)) return 'mp3';
    if (format.indexOf('m4a') >= 0 || format.indexOf('mpeg-4 audio') >= 0 || /\.m4a$/.test(name)) return 'm4a';
    return null;
  }

  function positiveInteger(value) {
    var number = Number(value);
    return isFinite(number) && number > 0 ? Math.floor(number) : null;
  }

  function bitDepthOf(file) {
    var direct = positiveInteger(file.bitdepth || file.bit_depth);
    var matched = String(file.format || '').match(/(\d{1,2})\s*bit/i);
    var depth = direct || (matched ? Number(matched[1]) : null);
    return depth >= 8 && depth <= 32 ? depth : null;
  }

  function sampleRateOf(file) {
    var value = file.sample_rate || file.samplerate || file.sampleRate;
    if (value == null) return null;
    var text = String(value).toLowerCase().replace(/\s+/g, '');
    var matched = text.match(/^(\d+(?:\.\d+)?)(khz|hz)?$/);
    if (!matched) return null;
    var rate = Number(matched[1]) * (matched[2] === 'khz' ? 1000 : 1);
    rate = Math.round(rate);
    return rate >= 8000 && rate <= 768000 ? rate : null;
  }

  function encodePath(value) {
    return String(value || '').split('/').map(function (part) { return encodeURIComponent(part); }).join('/');
  }

  function fileDescriptor(identifier, file) {
    var format = formatOf(file);
    if (!format || !file.name) return null;
    var descriptor = {
      url: DOWNLOAD_URL + encodeURIComponent(identifier) + '/' + encodePath(file.name),
      format: format,
      provider: 'Internet Archive · CC'
    };
    var size = positiveInteger(file.size);
    var bitDepth = bitDepthOf(file);
    var sampleRate = sampleRateOf(file);
    if (size != null) descriptor.sizeHint = size;
    if (bitDepth != null) descriptor.bitDepth = bitDepth;
    if (sampleRate != null) descriptor.sampleRate = sampleRate;
    return descriptor;
  }

  function exactFiles(item, document, track) {
    var metadata = item && item.metadata ? item.metadata : {};
    if (!allowedLicence(metadata.licenseurl || document.licenseurl)) return [];
    if (!artistMatches(metadata.creator || document.creator, track)) return [];
    if (item.is_dark === true || item.is_dark === 1 || item.is_dark === '1') return [];

    var wantedTitles = titleKeys(track.title);
    var identifier = String(metadata.identifier || document.identifier || '');
    if (!identifier || !wantedTitles.length) return [];

    return list(item.files).filter(function (file) {
      if (!file || file.private === true || file.private === 'true') return false;
      if (!formatOf(file)) return false;
      if (!intersects(candidateTitles(file), wantedTitles)) return false;
      var fileArtist = file.artist || file.creator;
      if (fileArtist && !artistMatches(fileArtist, track)) return false;
      return durationMatches(file, track);
    }).map(function (file) {
      return fileDescriptor(identifier, file);
    }).filter(function (file) { return file != null; });
  }

  function lucene(value) {
    return String(value || '').replace(/([+\-&|!(){}\[\]^"~*?:\\/])/g, '\\$1');
  }

  function searchUrl(track, broad, rows) {
    var artist = lucene(track.artist || first(track.artists));
    var query = 'mediatype:audio AND licenseurl:* AND creator:"' + artist + '"';
    if (!broad) {
      var choices = ['title:"' + lucene(track.title) + '"'];
      if (track.album) choices.push('title:"' + lucene(track.album) + '"');
      query += ' AND (' + choices.join(' OR ') + ')';
    }
    return SEARCH_URL + '?q=' + encodeURIComponent(query) +
      '&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=creator&fl%5B%5D=licenseurl' +
      '&sort%5B%5D=downloads+desc&rows=' + rows + '&page=1&output=json';
  }

  function responseOutcome(response) {
    if (!response) return outcome('network', {
      detail: message('Internet Archive did not answer', 'Internet Archive no respondió')
    });
    if (response.error) return outcome('network', {
      detail: message('Internet Archive is not reachable', 'No se puede conectar con Internet Archive')
    });
    if (response.status === 429) {
      var retry = Number((response.headers || {})['retry-after'] || 60) * 1000;
      return outcome('rate-limited', { retryAfterMs: retry });
    }
    if (response.status >= 500) return outcome('server-down', { retryAfterMs: 300000 });
    if (!response.ok) return outcome('error', {
      detail: message('Internet Archive refused the request', 'Internet Archive rechazó la solicitud')
    });
    return null;
  }

  function search(track, broad, rows) {
    var response = myspoti.http.get(searchUrl(track, broad, rows), { timeout: 7000 });
    var failed = responseOutcome(response);
    if (failed) return { documents: [], failure: failed };
    try {
      var body = response.json();
      return { documents: list(body && body.response && body.response.docs), failure: null };
    } catch (error) {
      myspoti.log('Internet Archive search JSON:', error.message || error);
      return { documents: [], failure: outcome('error', {
        detail: message('Internet Archive returned unreadable metadata', 'Internet Archive devolvió metadatos ilegibles')
      }) };
    }
  }

  function metadataResponses(documents) {
    var responses = [];
    var requests = documents.map(function (document) {
      return { url: METADATA_URL + encodeURIComponent(document.identifier), method: 'GET', timeout: 7000 };
    });
    for (var offset = 0; offset < requests.length; offset += 4) {
      var batch = requests.slice(offset, offset + 4);
      if (supports('http.all')) {
        responses = responses.concat(myspoti.http.all(batch));
      } else {
        batch.forEach(function (request) {
          try {
            responses.push(myspoti.http.get(request.url, { timeout: request.timeout }));
          } catch (error) {
            responses.push({ error: String(error && error.message || error) });
          }
        });
      }
    }
    return responses;
  }

  function resolve(documents, track, seen) {
    var fresh = documents.filter(function (document) {
      var identifier = String(document.identifier || '');
      if (!identifier || seen[identifier]) return false;
      seen[identifier] = true;
      return true;
    });
    if (!fresh.length) return { files: [], failure: null };

    var responses = metadataResponses(fresh);
    var files = [];
    var failures = [];
    responses.forEach(function (response, index) {
      var failed = responseOutcome(response);
      if (failed) { failures.push(failed); return; }
      try {
        files = files.concat(exactFiles(response.json(), fresh[index], track));
      } catch (error) {
        myspoti.log('Internet Archive item JSON:', error.message || error);
      }
    });
    return { files: files, failure: files.length ? null : (failures.length === responses.length ? failures[0] : null) };
  }

  function ranked(files, quality) {
    var preference = quality === 'small' ? { mp3: 0, m4a: 1, flac: 2 } : { flac: 0, m4a: 1, mp3: 2 };
    var unique = {};
    return files.filter(function (file) {
      if (unique[file.url]) return false;
      unique[file.url] = true;
      return true;
    }).sort(function (left, right) {
      var byFormat = preference[left.format] - preference[right.format];
      if (byFormat) return byFormat;
      if (quality === 'small') return (left.sizeHint || Number.MAX_VALUE) - (right.sizeHint || Number.MAX_VALUE);
      return (right.sizeHint || 0) - (left.sizeHint || 0);
    }).slice(0, 10);
  }

  myspoti.provide('download-source', function (track) {
    try {
      if (!track || !track.title || !(track.artist || list(track.artists).length)) {
        return outcome('not-found');
      }

      var seen = {};
      var strictSearch = search(track, false, MAX_STRICT_ITEMS);
      if (strictSearch.failure) return strictSearch.failure;
      var strict = resolve(strictSearch.documents, track, seen);
      if (strict.files.length) return ranked(strict.files, track.quality);
      if (strict.failure) return strict.failure;

      var broadSearch = search(track, true, MAX_BROAD_ITEMS);
      if (broadSearch.failure) return broadSearch.failure;
      var broad = resolve(broadSearch.documents, track, seen);
      if (broad.files.length) return ranked(broad.files, track.quality);
      return broad.failure || outcome('not-found');
    } catch (error) {
      myspoti.log('Open Music Downloads:', error.message || error);
      return outcome('network', {
        detail: message('Internet Archive is not reachable', 'No se puede conectar con Internet Archive')
      });
    }
  });

  myspoti.provide('status', function () {
    try {
      var url = SEARCH_URL + '?q=identifier%3A__orpheon_status__&rows=0&output=json';
      var response = myspoti.http.get(url, { timeout: 4000 });
      if (response.ok) return { live: true };
      return {
        live: false,
        detail: message('Internet Archive is unavailable (' + response.status + ')', 'Internet Archive no está disponible (' + response.status + ')')
      };
    } catch (error) {
      return {
        live: false,
        detail: message('Internet Archive is not reachable', 'No se puede conectar con Internet Archive')
      };
    }
  });
}());
