from ocdsdata import database
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cove_ocds.settings")  # noqa
from cove_ocds.lib.api import ocds_json_output, APIException
import sqlalchemy as sa
import tempfile
import shutil


def handle_package(package):
    cove_temp_folder = tempfile.mkdtemp(prefix='ocdsdata-cove-', dir=tempfile.gettempdir())
    try:
        return ocds_json_output(cove_temp_folder, None, None, convert=False, cache_schema=True, file_type='json', json_data=package)
    finally:
        shutil.rmtree(cove_temp_folder)


def get_package_data(package_data_id):
    with database.engine.begin() as connection:
        s = sa.sql.select([database.package_data_table]) \
            .where(database.package_data_table.c.id == package_data_id)
        result = connection.execute(s)
        data_row = result.fetchone()
        return data_row['data']


def get_data(data_id):
    with database.engine.begin() as connection:
        s = sa.sql.select([database.data_table]) \
            .where(database.data_table.c.id == data_id)
        result = connection.execute(s)
        data_row = result.fetchone()
        return data_row['data']


def check_file(source, source_session_id, file_info):

    file_id = database.get_id_of_store_file(source_session_id, file_info)

    with database.engine.begin() as connection:

        release_rows = connection.execute(
            database.release_table.select().where(database.release_table.c.source_session_file_status_id == file_id)
        )

    for release_row in release_rows:
        if not database.is_release_check_done(release_row['id']):
            check_release_row(source, release_row)

    del release_rows

    with database.engine.begin() as connection:

        record_rows = connection.execute(
            database.record_table.select().where(database.record_table.c.source_session_file_status_id == file_id)
        )

    for record_row in record_rows:
        if not database.is_record_check_done(record_row['id']):
            check_record_row(source, record_row)


def check_release_row(source, release_row):
    package = get_package_data(release_row.package_data_id)
    package['releases'] = [get_data(release_row.data_id)]
    package = source.before_check_data(package)
    try:
        cove_output = handle_package(package)
        checks = [{
            'release_id': release_row.id,
            'cove_output': cove_output,
        }]
        with database.engine.begin() as connection:
            connection.execute(database.release_check_table.insert(), checks)
    except APIException as err:
        checks = [{
            'release_id': release_row.id,
            'error': str(err)
        }]
        with database.engine.begin() as connection:
            connection.execute(database.release_check_error_table.insert(), checks)


def check_record_row(source, record_row):
    package = get_package_data(record_row.package_data_id)
    package['records'] = [get_data(record_row.data_id)]
    package = source.before_check_data(package)
    try:
        cove_output = handle_package(package)
        checks = [{
            'record_id': record_row.id,
            'cove_output': cove_output,
        }]
        with database.engine.begin() as connection:
            connection.execute(database.record_check_table.insert(), checks)
    except APIException as err:
        checks = [{
            'record_id': record_row.id,
            'error': str(err)
        }]
        with database.engine.begin() as connection:
            connection.execute(database.record_check_error_table.insert(), checks)
