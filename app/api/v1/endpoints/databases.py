"""Routes pour la gestion des bases de données."""
import hashlib
from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy import text

from app.api.dependencies import get_session_manager
from app.services.session_manager2 import SessionManager
from app.services.ingest import create_data_frame
from app.db.connector import connect_db
from app.models.db_config import DBConfigBase, DBConfig
from app.models.response_data import DataResponses
from app.models.types import DBType

router = APIRouter()

@router.post("/test_connection")
async def test_connection(db_config: DBConfigBase = Body(...)):
    """Test database connection."""
    try:
        connection = await connect_db(db_config=db_config)
        with connection as conn:
            query = text("SELECT 1 FROM dual" if db_config.db_type == DBType.ORACLE else "SELECT 1")
            conn.execute(query)
        return {
            "message": f"Connection with {db_config.db_type} is established successfully",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/upload_sql_data")
async def upload_sql_data(
    db_config: DBConfig = Body(...),
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Upload data from SQL database."""
    try:
        table_data, dataframes = await create_data_frame(db_config=db_config)
        config = db_config.model_dump_json()
        session_id = hashlib.md5(config.encode()).hexdigest()

        session_manager.create_session(
            session_id=session_id,
            dataframes=dataframes,
            table_data=table_data,
            source_type="database"
        )

        return {
            "session_id": session_id,
            "data_responses": DataResponses(
                db_type=db_config.db_type,
                database=db_config.db,
                message=f"Loaded {len(table_data)} tables",
                total_tables=len(table_data),
                data_tables=table_data
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload database data: {str(e)}")