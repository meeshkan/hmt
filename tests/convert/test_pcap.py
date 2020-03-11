from meeshkan.convert.pcap import convert_pcap
from hamcrest import assert_that, has_length, has_entry

PCAP_SAMPLE = "tests/convert/recordings/recordings.pcap"


def test_convert_pcap():
    recordings_gen = convert_pcap(PCAP_SAMPLE)
    recordings = list(recordings_gen)
    assert_that(recordings, has_length(168))
    assert recordings[0].request.path == "/user/repos"
