from collections import Counter
from decimal import Decimal

import pytest

from commons_codec.transform.dynamodb import CrateDBTypeDeserializer, DynamoCDCTranslatorCrateDB

READING_BASIC = {"device": "foo", "temperature": 42.42, "humidity": 84.84}

MSG_UNKNOWN_SOURCE = {
    "eventSource": "foo:bar",
}
MSG_UNKNOWN_EVENT = {
    "eventSource": "aws:dynamodb",
    "eventName": "FOOBAR",
}

MSG_INSERT_BASIC = {
    "awsRegion": "us-east-1",
    "eventID": "b015b5f0-c095-4b50-8ad0-4279aa3d88c6",
    "eventName": "INSERT",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720740233012995,
        "Keys": {"device": {"S": "foo"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "NewImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "device": {"S": "foo"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
            "string_set": {"SS": ["location_1"]},
            "number_set": {"NS": [1, 2, 3, 4]},
            "binary_set": {"BS": ["U3Vubnk="]},
        },
        "SizeBytes": 99,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_INSERT_NESTED = {
    "awsRegion": "us-east-1",
    "eventID": "b581c2dc-9d97-44ed-94f7-cb77e4fdb740",
    "eventName": "INSERT",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "table-testdrive-nested",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720800199717446,
        "Keys": {"id": {"S": "5F9E-Fsadd41C-4C92-A8C1-70BF3FFB9266"}},
        "NewImage": {
            "id": {"S": "5F9E-Fsadd41C-4C92-A8C1-70BF3FFB9266"},
            "data": {"M": {"temperature": {"N": "42.42"}, "humidity": {"N": "84.84"}}},
            "meta": {"M": {"timestamp": {"S": "2024-07-12T01:17:42"}, "device": {"S": "foo"}}},
            "string_set": {"SS": ["location_1"]},
            "number_set": {"NS": [1, 2, 3, 0.34]},
            "binary_set": {"BS": ["U3Vubnk="]},
            "somemap": {
                "M": {
                    "test": {"N": 1},
                    "test2": {"N": 2},
                }
            },
        },
        "SizeBytes": 156,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_MODIFY_BASIC = {
    "awsRegion": "us-east-1",
    "eventID": "24757579-ebfd-480a-956d-a1287d2ef707",
    "eventName": "MODIFY",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720742302233719,
        "Keys": {"device": {"S": "foo"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "NewImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "55.66"},
            "device": {"S": "bar"},
            "location": {"S": "Sydney"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
            "string_set": {"SS": ["location_1"]},
            "number_set": {"NS": [1, 2, 3, 0.34]},
            "binary_set": {"BS": ["U3Vubnk="]},
            "empty_string": {"S": ""},
            "null_string": {"S": None},
        },
        "OldImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "device": {"S": "foo"},
            "location": {"S": "Sydney"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
        },
        "SizeBytes": 161,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_MODIFY_NESTED = {
    "awsRegion": "us-east-1",
    "eventID": "24757579-ebfd-480a-956d-a1287d2ef707",
    "eventName": "MODIFY",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720742302233719,
        "Keys": {"device": {"S": "foo"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "NewImage": {
            "device": {"M": {"id": {"S": "bar"}, "serial": {"N": 12345}}},
            "tags": {"L": [{"S": "foo"}, {"S": "bar"}]},
            "empty_map": {"M": {}},
            "empty_list": {"L": []},
            "timestamp": {"S": "2024-07-12T01:17:42"},
            "string_set": {"SS": ["location_1"]},
            "number_set": {"NS": [1, 2, 3, 0.34]},
            "binary_set": {"BS": ["U3Vubnk="]},
            "somemap": {
                "M": {
                    "test": {"N": 1},
                    "test2": {"N": 2},
                }
            },
            "list_of_objects": {"L": [{"M": {"foo": {"S": "bar"}}}, {"M": {"baz": {"S": "qux"}}}]},
        },
        "OldImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "42.42"},
            "location": {"S": "Sydney"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
            "device": {"M": {"id": {"S": "bar"}, "serial": {"N": 12345}}},
        },
        "SizeBytes": 161,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}
MSG_REMOVE = {
    "awsRegion": "us-east-1",
    "eventID": "ff4e68ab-0820-4a0c-80b2-38753e8e00e5",
    "eventName": "REMOVE",
    "userIdentity": None,
    "recordFormat": "application/json",
    "tableName": "foo",
    "dynamodb": {
        "ApproximateCreationDateTime": 1720742321848352,
        "Keys": {"device": {"S": "bar"}, "timestamp": {"S": "2024-07-12T01:17:42"}},
        "OldImage": {
            "humidity": {"N": "84.84"},
            "temperature": {"N": "55.66"},
            "device": {"S": "bar"},
            "timestamp": {"S": "2024-07-12T01:17:42"},
            "string_set": {"SS": ["location_1"]},
            "number_set": {"NS": [1, 2, 3, 0.34]},
            "binary_set": {"BS": ["U3Vubnk="]},
            "somemap": {
                "M": {
                    "test": {"N": 1},
                    "test2": {"N": 2},
                }
            },
        },
        "SizeBytes": 99,
        "ApproximateCreationDateTimePrecision": "MICROSECOND",
    },
    "eventSource": "aws:dynamodb",
}


def test_decode_ddb_deserialize_type():
    assert DynamoCDCTranslatorCrateDB(table_name="foo").deserialize_item({"foo": {"N": "84.84"}}) == {"foo": 84.84}


def test_decode_cdc_sql_ddl():
    assert DynamoCDCTranslatorCrateDB(table_name="foo").sql_ddl == 'CREATE TABLE "foo" (data OBJECT(DYNAMIC));'


def test_decode_cdc_unknown_source():
    with pytest.raises(ValueError) as ex:
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_UNKNOWN_SOURCE)
    assert ex.match("Unknown eventSource: foo:bar")


def test_decode_cdc_unknown_event():
    with pytest.raises(ValueError) as ex:
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_UNKNOWN_EVENT)
    assert ex.match("Unknown CDC event name: FOOBAR")


def test_decode_cdc_insert_basic():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_INSERT_BASIC) == 'INSERT INTO "foo" (data) '
        'VALUES (\'{"humidity": 84.84, "temperature": 42.42, "device": "foo", "timestamp": "2024-07-12T01:17:42",'
        ' "string_set": ["location_1"], "number_set": [1.0, 2.0, 3.0, 4.0], "binary_set": ["U3Vubnk="]}\');'
    )


def test_decode_cdc_insert_nested():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_INSERT_NESTED)
        == 'INSERT INTO "foo" (data) VALUES (\'{"id": "5F9E-Fsadd41C-4C92-A8C1-70BF3FFB9266", '
        '"data": {"temperature": 42.42, "humidity": 84.84}, '
        '"meta": {"timestamp": "2024-07-12T01:17:42", "device": "foo"},'
        ' "string_set": ["location_1"], "number_set": [0.34, 1.0, 2.0, 3.0],'
        ' "binary_set": ["U3Vubnk="], "somemap": {"test": 1.0, "test2": 2.0}}\');'
    )


def test_decode_cdc_modify_basic():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_MODIFY_BASIC) == 'UPDATE "foo" '
        "SET data['humidity'] = 84.84, data['temperature'] = 55.66, data['location'] = 'Sydney', "
        "data['string_set'] = ['location_1'], data['number_set'] = [0.34, 1.0, 2.0, 3.0],"
        " data['binary_set'] = ['U3Vubnk='], data['empty_string'] = '', data['null_string'] = NULL"
        " WHERE data['device'] = 'foo' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )


def test_decode_cdc_modify_nested():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_MODIFY_NESTED) == 'UPDATE "foo" '
        "SET data['tags'] = ['foo', 'bar'], data['empty_map'] = '{}'::OBJECT, data['empty_list'] = [],"
        " data['string_set'] = ['location_1'], data['number_set'] = [0.34, 1.0, 2.0, 3.0],"
        " data['binary_set'] = ['U3Vubnk='], data['somemap'] = '{\"test\": 1.0, \"test2\": 2.0}'::OBJECT,"
        ' data[\'list_of_objects\'] = \'[{"foo": "bar"}, {"baz": "qux"}]\'::OBJECT[]'
        " WHERE data['device'] = 'foo' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )


def test_decode_cdc_remove():
    assert (
        DynamoCDCTranslatorCrateDB(table_name="foo").to_sql(MSG_REMOVE) == 'DELETE FROM "foo" '
        "WHERE data['device'] = 'bar' AND data['timestamp'] = '2024-07-12T01:17:42';"
    )


def test_deserialize_number_set():
    deserializer = CrateDBTypeDeserializer()
    assert deserializer.deserialize({"NS": ["1", "1.25"]}) == [
        Decimal("1"),
        Decimal("1.25"),
    ]


def test_deserialize_string_set():
    deserializer = CrateDBTypeDeserializer()
    # We us Counter because when the set is transformed into a list, it loses order.
    assert Counter(deserializer.deserialize({"SS": ["foo", "bar"]})) == Counter(
        [
            "foo",
            "bar",
        ]
    )


def test_deserialize_binary_set():
    deserializer = CrateDBTypeDeserializer()
    assert Counter(deserializer.deserialize({"BS": [b"\x00", b"\x01"]})) == Counter([b"\x00", b"\x01"])


def test_deserialize_list_objects():
    deserializer = CrateDBTypeDeserializer()
    assert deserializer.deserialize(
        {
            "L": [
                {
                    "M": {
                        "foo": {"S": "mystring"},
                        "bar": {"M": {"baz": {"N": "1"}}},
                    }
                },
                {
                    "M": {
                        "foo": {"S": "other string"},
                        "bar": {"M": {"baz": {"N": "2"}}},
                    }
                },
            ]
        }
    )
