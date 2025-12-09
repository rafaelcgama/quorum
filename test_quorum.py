import os
import pandas as pd
import pandas.testing as pdt

from main import merge_votes, compute_legislator_support, compute_bill_support_counts


def make_mock_data():
    """Create a minimal, consistent set of mock data for tests."""

    # bills: 2 bills, one with sponsor, one without
    bills = pd.DataFrame(
        [
            {"id": 10, "title": "Bill A", "sponsor_id": 1},
            {"id": 11, "title": "Bill B", "sponsor_id": None},
        ]
    )

    # legislators: 3 total, one will never vote
    legislators = pd.DataFrame(
        [
            {"id": 1, "name": "Biden"},
            {"id": 2, "name": "Trump"},
            {"id": 3, "name": "Sanders"},  # never votes
        ]
    )

    # votes: link vote_id -> bill_id
    votes = pd.DataFrame(
        [
            {"id": 100, "bill_id": 10},
            {"id": 101, "bill_id": 11},
        ]
    )

    # vote_results: actual legislator votes with type
    # vote_type: 1 = yes, 2 = no
    vote_results = pd.DataFrame(
        [
            {"id": 1, "legislator_id": 1, "vote_id": 100, "vote_type": 1},  # Biden yes on 10
            {"id": 2, "legislator_id": 2, "vote_id": 100, "vote_type": 2},  # Trump no on 10
            {"id": 3, "legislator_id": 2, "vote_id": 101, "vote_type": 1},  # Trump yes on 11
            # Sanders never appears here
        ]
    )

    return bills, legislators, vote_results, votes


def test_merge_votes_basic():
    """merge_votes should attach bill_id using vote_id."""

    bills, legislators, vote_results, votes = make_mock_data()
    vr = merge_votes(vote_results, votes)

    # Expected result: same rows as vote_results, but with bill_id column added
    expected = vote_results.copy()
    expected = expected.merge(votes.rename(columns={"id": "vote_id"})[["vote_id", "bill_id"]], on="vote_id")

    pdt.assert_frame_equal(
        vr.sort_values(["vote_id", "legislator_id"]).reset_index(drop=True),
        expected.sort_values(["vote_id", "legislator_id"]).reset_index(drop=True),
    )


def test_compute_legislator_support_counts():
    """
    - Biden: 1 yes (bill 10), 0 no
    - Trump: 1 yes (bill 11), 1 no (bill 10)
    - Sanders: never voted -> should NOT appear
    """

    bills, legislators, vote_results, votes = make_mock_data()
    vr = merge_votes(vote_results, votes)

    result = compute_legislator_support(vr, legislators).sort_values("id").reset_index(drop=True)

    expected = pd.DataFrame(
        [
            {"id": 1, "name": "Biden", "num_supported_bills": 1, "num_opposed_bills": 0},
            {"id": 2, "name": "Trump", "num_supported_bills": 1, "num_opposed_bills": 1},
            # Sanders (id 3) never appears because he never voted
        ]
    )

    pdt.assert_frame_equal(result, expected)


def test_compute_legislator_support_only_yes_or_no():
    """
    Edge case:
    - Legislator only ever votes yes -> opposed should be 0
    - Legislator only ever votes no  -> supported should be 0
    """

    legislators = pd.DataFrame(
        [
            {"id": 1, "name": "yes_only"},
            {"id": 2, "name": "no_only"},
        ]
    )

    vr = pd.DataFrame(
        [
            {"vote_id": 100, "legislator_id": 1, "bill_id": 10, "vote_type": 1},
            {"vote_id": 101, "legislator_id": 1, "bill_id": 11, "vote_type": 1},
            {"vote_id": 102, "legislator_id": 2, "bill_id": 12, "vote_type": 2},
        ]
    )

    result = compute_legislator_support(vr, legislators).sort_values("id").reset_index(drop=True)

    expected = pd.DataFrame(
        [
            {"id": 1, "name": "yes_only", "num_supported_bills": 2, "num_opposed_bills": 0},
            {"id": 2, "name": "no_only", "num_supported_bills": 0, "num_opposed_bills": 1},
        ]
    )

    pdt.assert_frame_equal(result, expected)


def test_compute_bill_support_counts_and_unknown_sponsor():
    """
    - Bill 10: 1 yes (Biden), 1 no (Trump), sponsor_id=1 -> 'Biden'
    - Bill 11: 1 yes (Trump),  0 no,       sponsor_id=None -> 'Unknown'
    """

    bills, legislators, vote_results, votes = make_mock_data()
    vr = merge_votes(vote_results, votes)

    result = compute_bill_support_counts(vr, bills, legislators).sort_values("id").reset_index(drop=True)

    expected = pd.DataFrame(
        [
            {
                "id": 10,
                "title": "Bill A",
                "supporter_count": 1,
                "opposer_count": 1,
                "primary_sponsor": "Biden",
            },
            {
                "id": 11,
                "title": "Bill B",
                "supporter_count": 1,
                "opposer_count": 0,
                "primary_sponsor": "Unknown",
            },
        ]
    )

    pdt.assert_frame_equal(result, expected)


def test_bill_with_no_votes_has_zero_counts():
    """
    If a bill has no votes at all, it should still appear
    with supporter/opposer counts = 0.
    """

    bills = pd.DataFrame(
        [
            {"id": 10, "title": "Bill A", "sponsor_id": None},
            {"id": 11, "title": "Bill B", "sponsor_id": None},
        ]
    )

    legislators = pd.DataFrame(
        [
            {"id": 1, "name": "Biden"},
        ]
    )

    # Only bill 10 has a vote
    vr = pd.DataFrame(
        [
            {"vote_id": 100, "legislator_id": 1, "bill_id": 10, "vote_type": 1},
        ]
    )

    result = compute_bill_support_counts(vr, bills, legislators).sort_values("id").reset_index(drop=True)

    expected = pd.DataFrame(
        [
            {
                "id": 10,
                "title": "Bill A",
                "supporter_count": 1,
                "opposer_count": 0,
                "primary_sponsor": "Unknown",
            },
            {
                "id": 11,
                "title": "Bill B",
                "supporter_count": 0,
                "opposer_count": 0,
                "primary_sponsor": "Unknown",
            },
        ]
    )

    pdt.assert_frame_equal(result, expected)


def test_main_runs_end_to_end(tmp_path, monkeypatch):
    """Integration test — runs full pipeline and checks output files exist."""

    from main import main  # adjust import if file name differs

    monkeypatch.chdir(tmp_path)  # run in isolated temp directory
    os.makedirs("data", exist_ok=True)

    # Write minimal input CSVs
    pd.DataFrame([{"id": 10, "title": "Bill A", "sponsor_id": None}]).to_csv("data/bills.csv", index=False)
    pd.DataFrame([{"id": 1, "name": "Biden"}]).to_csv("data/legislators.csv", index=False)
    pd.DataFrame([{"id": 1, "legislator_id": 1, "vote_id": 100, "vote_type": 1}]).to_csv("data/vote_results.csv", index=False)
    pd.DataFrame([{"id": 100, "bill_id": 10}]).to_csv("data/votes.csv", index=False)

    main()  # now everything runs

    assert os.path.exists("output/legislators-support-oppose-count.csv")
    assert os.path.exists("output/bills.csv")
