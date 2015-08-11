from functools import partial

from validator import decorator
from validator import metadata_helpers


@decorator.register_test(tier=1)
def test_package_json_params(err, xpi_package=None):
    if err.get_resource('has_package_json'):
        validate_required_field(err, 'id', validate_id)
        validate_required_field(err, 'name', validate_name)
        validate_required_field(err, 'version', validate_version)


def validate_required_field(err, field, validate_fn):
    package_json = err.get_resource('package_json')
    if field in package_json:
        value = package_json[field]
        validate_fn(err, value)
    else:
        err.error(
            ('package_json', 'field_required', field),
            'Your package.json is missing a required field',
            'Your package.json is missing the "{field}" field.'.format(
                field=field))


validate_id = partial(metadata_helpers.validate_id, source='package.json')
validate_version = partial(
    metadata_helpers.validate_version, source='package.json')
validate_name = partial(metadata_helpers.validate_name, source='package.json')
