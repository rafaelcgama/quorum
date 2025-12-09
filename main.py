import os
import pandas as pd


# ====================== Load ====================== #
def load_data(
        bills_path="data/bills.csv",
        legislators_path="data/legislators.csv",
        vote_results_path="data/vote_results.csv",
        votes_path="data/votes.csv",
):
    bills = pd.read_csv(bills_path)
    legislators = pd.read_csv(legislators_path)
    vote_results = pd.read_csv(vote_results_path)
    votes = pd.read_csv(votes_path)
    return bills, legislators, vote_results, votes


# ===================== Merge Helper ===================== #

def merge_votes(vote_results, votes):
    """Normalize and merge vote+result so we know which bill each vote belongs to."""
    votes = votes.rename(columns={"id": "vote_id"})  # normalize key
    return vote_results.merge(votes[["vote_id", "bill_id"]], on="vote_id")


# ================= Deliverable 1 ================== #

def compute_legislator_support(vr, legislators):
    """Return legislators that voted + how many bills they supported/opposed."""
    supported = vr[vr["vote_type"] == 1].groupby("legislator_id")["bill_id"].nunique()
    opposed = vr[vr["vote_type"] == 2].groupby("legislator_id")["bill_id"].nunique()

    voters = vr["legislator_id"].unique()
    result = legislators[legislators["id"].isin(voters)].copy()

    result["num_supported_bills"] = result["id"].map(supported).fillna(0).astype(int)
    result["num_opposed_bills"] = result["id"].map(opposed).fillna(0).astype(int)

    return result


# ================= Deliverable 2 ================== #

def compute_bill_support_counts(vr, bills, legislators):
    """Return bills with supporter/opposer counts + mapped sponsor names."""
    supporters = vr[vr["vote_type"] == 1].groupby("bill_id")["legislator_id"].nunique()
    opposers = vr[vr["vote_type"] == 2].groupby("bill_id")["legislator_id"].nunique()

    result = bills.copy()
    result["supporter_count"] = result["id"].map(supporters).fillna(0).astype(int)
    result["opposer_count"] = result["id"].map(opposers).fillna(0).astype(int)
    result["primary_sponsor"] = (
        result["sponsor_id"].map(legislators.set_index("id")["name"]).fillna("Unknown")
    )

    return result[["id", "title", "supporter_count", "opposer_count", "primary_sponsor"]]


# ===================== Main Run ===================== #

def main():
    bills, legislators, vote_results, votes = load_data()
    vr = merge_votes(vote_results, votes)

    os.makedirs("output", exist_ok=True)

    compute_legislator_support(vr, legislators).to_csv(
        "output/legislators-support-oppose-count.csv", index=False
    )
    compute_bill_support_counts(vr, bills, legislators).to_csv(
        "output/bills.csv", index=False
    )

    print("✔ Output generated in /output")


if __name__ == "__main__":
    main()
