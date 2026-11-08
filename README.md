# streamvault-epg-es

XMLTV guide for StreamVault whose channel names are the IPTV provider's exact `ES - …` names, so StreamVault matches every channel automatically (it only matches exact tvg-id or exact normalized display-name).

- Programmes come from [davidmuma/EPG_dobleM](https://github.com/davidmuma/EPG_dobleM) `guiatv.xml.gz` (Kodi colour tags stripped). Each provider variant (FHD/HD/HEVC/SD…) gets its own copy of the schedule.
- The genre from the source sub-title ("Deportes,Fútbol") becomes `<category>`, so StreamVault's Sports hub recognises sports. Spanish "Resumen/Previa/Postpartido/Reposición" titles also get the English category it understands ("Highlights", "Preview", "Post-game", "Replay"), so they aren't listed as live matches.
- `channels.txt` is the provider's ES channel list (names only). `make_epg.py` builds `guide.xml.gz`; the workflow rebuilds it every 6 h.

Guide URL: `https://raw.githubusercontent.com/juanfadev/streamvault-epg-es/main/guide.xml.gz`
