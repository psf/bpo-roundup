
This directory contains useful `detectors` and `extensions`, which
are both Roundup `plugins`.


### Plugins or Extensions

Historically, Roundup plugins were called `extensions`, then at some
point appeared specialized class of extensions called `detectors`.

`extensions` extend tracker instance adding new utils, actions and
(since 1.6.0) URL handlers for web part. `detectors` allow to change
the behavior of data model by adding reactors to data change events.

The API difference between `detector` and `extension` is that first
gets `db` argument for its `init()` function and the second gets
`tracker` instance. Both extend Roundup if placed into corresponding
directories of tracker home, so they both can be called in a more
familiar manner as `plugins`.
