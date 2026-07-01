from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from app.infrastructure.repositories import LogTestingRepository # Pastikan repo ini ada
from app.domain.models import LogTesting, Classification, ConclusionFeature, SensorMQ135, SensorDHT22

class LogTestingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LogTestingRepository(db)

    async def create_log(self, data: dict):
        """Membuat log testing baru."""
        new_log = LogTesting(**data)
        self.db.add(new_log)
        await self.db.commit()
        await self.db.refresh(new_log)
        return new_log  
    
    async def create_bulk_logs(self, logs_data: list): # logs_data berisi list of LogCreateSchema
        # Konversi setiap objek Pydantic menjadi dict
        logs_as_dicts = [log.model_dump() for log in logs_data]
        
        # Kirim list of dict ke repository
        return await self.repo.create_bulk_logs(logs_as_dicts)

    async def get_all_logs_detailed(self):
        stmt = (
            select(LogTesting)
            .options(
                # Kita harus masuk ke classification, lalu ke conclusion_feature, 
                # BARU setelah itu ke sensor_mq135/sensor_dht22
                joinedload(LogTesting.classification)
                .joinedload(Classification.conclusion_feature)
                .joinedload(ConclusionFeature.sensor_mq135),
                
                joinedload(LogTesting.classification)
                .joinedload(Classification.conclusion_feature)
                .joinedload(ConclusionFeature.sensor_dht22)
            )
            .order_by(LogTesting.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()