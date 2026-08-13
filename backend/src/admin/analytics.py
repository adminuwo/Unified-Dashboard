from typing import Dict, Any
from pymongo.database import Database  # type: ignore


def get_app_overlap_stats(db: Database) -> Dict[str, Any]:
    """Calculate registration and login crossover metrics between AISA, AI Legal, and other connected apps."""
    # Find AISA and AI Legal applications by name (case-insensitive)
    aisa_app = db["application_keys"].find_one({"application_name": {"$regex": "^aisa$", "$options": "i"}})
    legal_app = db["application_keys"].find_one({"application_name": {"$regex": "^ai\\s*legal(s)?$", "$options": "i"}})

    aisa_id = str(aisa_app["_id"]) if aisa_app else None
    legal_id = str(legal_app["_id"]) if legal_app else None

    # Compile user stats for all registered applications
    apps_cursor = db["application_keys"].find({"status": "active"})
    apps_list = []
    for app in apps_cursor:
        app_id = str(app["_id"])
        user_count = db["users"].count_documents({"connected_apps": app_id})
        apps_list.append({
            "id": app_id,
            "name": app.get("application_name", "Unknown"),
            "users_count": user_count
        })

    # Specialize stats for AISA & AI Legal
    aisa_users_count = db["users"].count_documents({"connected_apps": aisa_id}) if aisa_id else 0
    legal_users_count = db["users"].count_documents({"connected_apps": legal_id}) if legal_id else 0

    both_count = 0
    if aisa_id and legal_id:
        both_count = db["users"].count_documents({"connected_apps": {"$all": [aisa_id, legal_id]}})

    percentage_aisa = (both_count / aisa_users_count * 100) if aisa_users_count > 0 else 0.0
    percentage_legal = (both_count / legal_users_count * 100) if legal_users_count > 0 else 0.0

    # Cross-crossover matrix for all applications
    crossover_data = []
    for i in range(len(apps_list)):
        for j in range(i + 1, len(apps_list)):
            app1 = apps_list[i]
            app2 = apps_list[j]
            overlap_c = db["users"].count_documents({"connected_apps": {"$all": [app1["id"], app2["id"]]}})
            crossover_data.append({
                "app1_id": app1["id"],
                "app1_name": app1["name"],
                "app2_id": app2["id"],
                "app2_name": app2["name"],
                "overlap_count": overlap_c
            })

    total_users = db["users"].count_documents({})

    return {
        "total_users": total_users,
        "apps": apps_list,
        "aisa_app": {
            "found": aisa_app is not None,
            "id": aisa_id,
            "name": aisa_app["application_name"] if aisa_app else "AISA",
            "users_count": aisa_users_count
        },
        "ailegal_app": {
            "found": legal_app is not None,
            "id": legal_id,
            "name": legal_app["application_name"] if legal_app else "AI Legal",
            "users_count": legal_users_count
        },
        "overlap": {
            "count": both_count,
            "percentage_aisa": round(percentage_aisa, 2),
            "percentage_legal": round(percentage_legal, 2)
        },
        "crossover_matrix": crossover_data
    }
