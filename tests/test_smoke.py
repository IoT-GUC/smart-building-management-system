def test_read_main(client):
    response = client.get("/")
    # The root endpoint should redirect to /login
    assert response.status_code == 200 or response.status_code == 307
    if response.status_code == 200:
        assert b"LILYGO Provisioning Server" in response.content or b"Smart Building Management Server" in response.content

def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.content
