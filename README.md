# iDeezer

Playlist migration service from iTunes to Deezer.

### Run localy

* Register your own app on https://developers.deezer.com/myapps. Set "Application domain": `localhost`.
* Create `.env` file (in `.../root/root/.env`) with your application parameters (see `.env_example` for details).
* **Optionally**: download bootstrap v4.0.0 (https://getbootstrap.com) and copy bootstrap directory to `.../root/ideezer/static/` 
* Run via docker-compose from root directory:
```bash
docker-compose build
docker-compose up
```

### Music migration
* Open service main page (`http://localhost` by default).
* Authenticate in Deezer (by "Deezer auth" button in site menu).
* Go to "iTunes Library" / "Upload iTunes xml" and upload your "iTunes Library.xml" file (by default it should be at root of your itunes library directory).
* Wait for uploading and processing (result will be shown at "iTunes Library" / "Upload history")
* Go to "Main page" / "Playlists" and choose playlist you want migrate to Deezer.
* Press "Search tracks in Deezer" and then "Create in Deezer" buttons from playlist page. As the result you will be redirected to page with newly created playlist on deezer.com.
* ...
* Profit!

By the moment track search is *unconfigurable*, e.g. first track suggested by Deezer API will be chosen.
