from meeshkan.transform.tshark import convert_pcap
from hamcrest import assert_that, has_length, has_entry

PCAP_SAMPLE = 'resources/recordings.pcap'

def test_convert_pcap():
    recordings_gen = convert_pcap(PCAP_SAMPLE)
    recordings = list(recordings_gen)
    assert_that(recordings, has_length(168))
    assert_that(recordings[0], has_entry("req", has_entry("path", "/user/repos")))
