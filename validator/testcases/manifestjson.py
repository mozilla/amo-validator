from functools import partial

from validator import decorator
from validator import metadata_helpers


@decorator.register_test(tier=1)
def test_manifest_json_params(err, xpi_manifest=None):
    if err.get_resource('has_manifest_json'):
        validate_required_id(err)
        validate_required_field(err, 'name', validate_name)
        validate_required_field(err, 'version', validate_version)


def validate_required_id(err):
    manifest_json = err.get_resource('manifest_json').data
    if ('applications' in manifest_json and
            'gecko' in manifest_json['applications'] and
            'id' in manifest_json['applications']['gecko']):
        value = manifest_json['applications']['gecko']['id']
        validate_id(err, value)
    else:
        create_missing_field_error(err, 'id')


def validate_required_field(err, field, validate_fn):
    manifest_json = err.get_resource('manifest_json').data
    if field in manifest_json:
        value = manifest_json[field]
        validate_fn(err, value)
    else:
        create_missing_field_error(err, field)


def create_missing_field_error(err, field):
    err.error(
        ('manifest_json', 'field_required', field),
        'Your manifest.json is missing a required field',
        'Your manifest.json is missing the "{field}" field.'.format(
            field=field))


validate_id = partial(metadata_helpers.validate_id, source='manifest.json')
validate_version = partial(
    metadata_helpers.validate_version, source='manifest.json')
validate_name = partial(metadata_helpers.validate_name, source='manifest.json')
