# zisofs2-tools

zisofs2 extend zisofs and enable transparent compression on ISO images (ISO 9660). In comparision to original project:

- Support multiple compressors
- Allow files bigger than 4 GiB

## Why?

Transparent compression is really cool, but original project was very limited and not developed anymore. Maybe this can reactivate the intereset

## Why Python and not C?
Why not? It have all what I need without spending much time in debuging memory issues.

## Where can I used it?
Right now, nowhere. Is still in development. But helping developing/improoving or opening tickets in other projects to support it is very welcome.

## How is internally designed?
Is designed to be as much similar as possible to its original project (ZISOFSv1). More information can be found in zisofs_format.txt and zisofs2_format.txt