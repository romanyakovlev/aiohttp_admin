import pytest
import datetime
import aiohttp_admin
from aiohttp_admin.backends.sa import SAResource


@pytest.fixture
def create_admin(loop, create_app_and_client, postgres, sa_table):
    async def f(resource_name='test_post'):
        app, client = await create_app_and_client()
        admin = aiohttp_admin.setup(app, './')
        admin.add_resource(SAResource(postgres, sa_table, url=resource_name))
        return admin, client
    return f


@pytest.mark.run_loop
async def test_basic_rest(create_table, loop, postgres, create_admin):
    admin, client = await create_admin()
    rows = 10
    await create_table(rows)
    resp = await client.list('test_post')
    assert len(resp) == rows

    entity_id = resp[0]['id']
    entity = await client.detail('test_post', entity_id)
    assert entity == resp[0]


@pytest.mark.run_loop
async def test_list_pagination(create_table, loop, postgres, create_admin):
    rows = 25
    await create_table(rows)
    admin, client = await create_admin()

    all_rows = await client.list('test_post', page=1, per_page=30)
    assert len(all_rows) == rows
    all_ids = {r['id'] for r in all_rows}

    page1 = await client.list('test_post', page=1, per_page=15)
    page2 = await client.list('test_post', page=2, per_page=15)
    assert len(page1) == 15
    assert len(page2) == 10

    paged_ids = {r['id'] for r in page1 + page2}
    assert set(all_ids) == set(paged_ids)


@pytest.mark.run_loop
async def test_create(create_table, loop, postgres, create_admin):
    admin, client = await create_admin()
    rows = 1
    resource = 'test_post'
    await create_table(rows)

    entity = {'title': 'title test_create',
              'category': 'category field',
              'body': 'body field',
              'views': 42,
              'average_note': 0.1,
              'pictures': {'foo': 'bar', 'i': 5},
              'published_at': datetime.datetime.now(),
              'tags': [1, 2, 3],
              'status': 'c'}
    resp = await client.create(resource, entity)
    row_list = await client.list(resource)
    assert len(row_list) == rows + 1
    assert 'id' in resp
    assert resp['title'] == entity['title']
