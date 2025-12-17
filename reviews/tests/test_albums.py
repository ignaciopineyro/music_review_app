def test_create_album(client):
    data = {"title": "The Dark Side of the Moon", "artist": "Pink Floyd", "year": 1973}
    response = client.post("/albums/", json=data)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == data["title"]
    assert "id" in body


def test_get_album_by_id(client):
    album = {"title": "OK Computer", "artist": "Radiohead", "year": 1997}
    created = client.post("/albums/", json=album).json()

    response = client.get(f"/albums/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == album["title"]


def test_get_all_albums(client):
    response = client.get("/albums/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_album(client):
    album = client.post(
        "/albums/", json={"title": "Album X", "artist": "Artist Y", "year": 2000}
    ).json()

    updated_data = {"title": "Album X Updated", "artist": "Artist Y", "year": 2001}

    response = client.put(f"/albums/{album['id']}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["year"] == 2001


def test_delete_album(client):
    album = client.post(
        "/albums/", json={"title": "Delete Me", "artist": "Somebody", "year": 2024}
    ).json()

    response = client.delete(f"/albums/{album['id']}")
    assert response.status_code == 200

    response = client.get(f"/albums/{album['id']}")
    assert response.status_code == 404
