const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const script = fs.readFileSync(
  path.join(__dirname, '..', 'extensions', 'musica-abierta', 'main.js'),
  'utf8'
);

function response(status, body, headers = {}) {
  return {
    status,
    headers,
    ok: status >= 200 && status < 300,
    body: typeof body === 'string' ? body : JSON.stringify(body),
    json() {
      if (typeof body === 'string') return JSON.parse(body);
      return body;
    }
  };
}

function plain(value) {
  return value == null ? value : JSON.parse(JSON.stringify(value));
}

function searchBody(documents) {
  return { response: { numFound: documents.length, docs: documents } };
}

function fixture(overrides = {}) {
  const document = {
    identifier: 'cafe-sur-luz-del-mar',
    title: 'Luz del mar',
    creator: 'Café Sur',
    licenseurl: 'https://creativecommons.org/licenses/by/4.0/'
  };
  const item = {
    metadata: { ...document },
    files: [
      {
        name: '01 - Canción Azul.flac',
        title: 'Canción Azul',
        artist: 'Café Sur',
        format: '24bit Flac',
        sample_rate: '96 kHz',
        length: '3:30',
        size: '42100000'
      },
      {
        name: '01 - Canción Azul.mp3',
        title: 'Canción Azul',
        artist: 'Café Sur',
        format: 'VBR MP3',
        length: '210.2',
        size: '6200000'
      }
    ]
  };
  return {
    document: { ...document, ...(overrides.document || {}) },
    item: {
      ...item,
      ...(overrides.item || {}),
      metadata: { ...item.metadata, ...(overrides.metadata || {}) },
      files: overrides.files || item.files
    }
  };
}

function loadExtension({ responder, features = ['results', 'http.all'], locale = 'es-UY' }) {
  const hooks = {};
  const requests = [];
  const logs = [];

  function send(url, options = {}) {
    requests.push({ url, options });
    const answer = responder(url, options, requests.length);
    if (answer instanceof Error) throw answer;
    return answer;
  }

  const myspoti = {
    features,
    locale,
    provide(name, fn) { hooks[name] = fn; },
    log(...values) { logs.push(values.join(' ')); },
    http: {
      get(url, options) { return send(url, options); },
      all(batch) {
        return batch.map((request) => {
          try {
            return send(request.url, request);
          } catch (error) {
            return { error: `http: ${error.message}` };
          }
        });
      }
    }
  };

  vm.runInNewContext(script, { myspoti, Object, Array, String, Number, Math, JSON, RegExp, Error, isFinite, encodeURIComponent });
  return { hooks, requests, logs };
}

function track(quality = 'cd') {
  return {
    id: 'spotify-id',
    uri: 'spotify:track:spotify-id',
    title: 'Canción Azul',
    artist: 'Café Sur',
    artists: ['Café Sur'],
    album: 'Luz del mar',
    durationMs: 210000,
    quality
  };
}

function archiveResponder(data, searchStatus = 200) {
  return (url) => {
    if (url.startsWith('https://archive.org/advancedsearch.php')) {
      return response(searchStatus, searchStatus === 200 ? searchBody([data.document]) : {});
    }
    if (url === `https://archive.org/metadata/${encodeURIComponent(data.document.identifier)}`) {
      return response(200, data.item);
    }
    throw new Error(`unexpected URL: ${url}`);
  };
}

test('returns exact openly licensed FLAC and MP3 matches', () => {
  const data = fixture();
  const runtime = loadExtension({ responder: archiveResponder(data) });
  const result = plain(runtime.hooks['download-source'](track('cd')));

  assert.equal(result.length, 2);
  assert.deepEqual(result.map((file) => file.format), ['flac', 'mp3']);
  assert.equal(result[0].provider, 'Internet Archive · CC');
  assert.equal(result[0].sizeHint, 42100000);
  assert.equal(result[0].bitDepth, 24);
  assert.equal(result[0].sampleRate, 96000);
  assert.match(result[0].url, /^https:\/\/archive\.org\/download\/cafe-sur-luz-del-mar\//);
  assert.match(result[0].url, /Canci%C3%B3n%20Azul\.flac$/);
  assert.ok(runtime.requests.every(({ url }) => new URL(url).hostname === 'archive.org'));
});

test('prefers the smaller MP3 for compact quality', () => {
  const data = fixture();
  const runtime = loadExtension({ responder: archiveResponder(data) });
  const result = plain(runtime.hooks['download-source'](track('small')));
  assert.deepEqual(result.map((file) => file.format), ['mp3', 'flac']);
});

test('rejects an item without an explicit Creative Commons or public-domain licence', () => {
  const data = fixture({ metadata: { licenseurl: 'https://example.com/custom-license' } });
  const runtime = loadExtension({ responder: archiveResponder(data) });
  assert.deepEqual(plain(runtime.hooks['download-source'](track())), { outcome: 'not-found' });
  assert.equal(runtime.requests.filter(({ url }) => url.includes('/metadata/')).length, 1);
});

test('accepts the Creative Commons public-domain mark', () => {
  const data = fixture({ metadata: { licenseurl: 'http://creativecommons.org/publicdomain/mark/1.0/' } });
  const runtime = loadExtension({ responder: archiveResponder(data) });
  const result = plain(runtime.hooks['download-source'](track()));
  assert.equal(result.length, 2);
});

test('handles Internet Archive artist arrays and semicolon-separated file creators', () => {
  const original = fixture();
  const files = original.item.files.map((file) => {
    const copy = { ...file, creator: 'Café Sur;Artista Invitado' };
    delete copy.artist;
    return copy;
  });
  const data = fixture({ metadata: { creator: ['Café Sur', 'Artista Invitado'] }, files });
  const runtime = loadExtension({ responder: archiveResponder(data) });
  assert.equal(plain(runtime.hooks['download-source'](track())).length, 2);
});

test('rejects a recording outside Orpheon duration bounds', () => {
  const data = fixture({
    files: [{
      name: 'Canción Azul.mp3', title: 'Canción Azul', artist: 'Café Sur',
      format: 'VBR MP3', length: '2:00', size: '4000000'
    }]
  });
  const runtime = loadExtension({ responder: archiveResponder(data) });
  assert.deepEqual(plain(runtime.hooks['download-source'](track())), { outcome: 'not-found' });
});

test('rejects a mismatched artist even when title and duration match', () => {
  const data = fixture({ metadata: { creator: 'Otro Artista' } });
  const runtime = loadExtension({ responder: archiveResponder(data) });
  assert.deepEqual(plain(runtime.hooks['download-source'](track())), { outcome: 'not-found' });
});

test('returns null on old hosts that do not understand outcomes', () => {
  const runtime = loadExtension({
    features: ['http.all'],
    responder(url) {
      if (url.startsWith('https://archive.org/advancedsearch.php')) return response(200, searchBody([]));
      throw new Error(`unexpected URL: ${url}`);
    }
  });
  assert.equal(runtime.hooks['download-source'](track()), null);
});

test('reports rate limiting with Retry-After', () => {
  const runtime = loadExtension({
    responder(url) {
      if (url.startsWith('https://archive.org/advancedsearch.php')) return response(429, {}, { 'retry-after': '45' });
      throw new Error(`unexpected URL: ${url}`);
    }
  });
  assert.deepEqual(plain(runtime.hooks['download-source'](track())), {
    outcome: 'rate-limited',
    retryAfterMs: 45000
  });
});

test('status is live on a successful Internet Archive response', () => {
  const runtime = loadExtension({ responder: () => response(200, searchBody([])) });
  assert.deepEqual(plain(runtime.hooks.status({})), { live: true });
});

test('status explains an unreachable source in Spanish', () => {
  const runtime = loadExtension({ responder: () => new Error('offline') });
  assert.deepEqual(plain(runtime.hooks.status({})), {
    live: false,
    detail: 'No se puede conectar con Internet Archive'
  });
});
