#!/usr/bin/env python3
"""
删除功能API路由
"""

import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from db import get_db
from models_magnet import MagnetLink
from routes.logs_routes import emit_log

router = APIRouter()

def clear_dashboard_cache():
    """清除仪表盘缓存"""
    try:
        from cache_manager import get_cache_manager
        cache = get_cache_manager()
        if cache.is_connected():
            cache.delete("dashboard:stats")
            print("✅ 仪表盘缓存已清除")
    except Exception as e:
        print(f"⚠️ 清除缓存失败: {e}")

@router.get("/api/delete/stats")
def get_delete_stats(db: Session = Depends(get_db)):
    """获取删除统计信息"""
    try:
        # 统计总数
        total_count = db.query(MagnetLink).count()
        
        # 统计有图片的记录
        with_images_count = db.query(MagnetLink).filter(
            MagnetLink.images.isnot(None),
            MagnetLink.images != ''
        ).count()
        
        # 统计测试数据
        test_keywords = ['test', '测试', 'workflow_test', 'downloaded_images_test']
        test_count = 0
        
        for keyword in test_keywords:
            count = db.query(MagnetLink).filter(
                MagnetLink.title.contains(keyword) |
                MagnetLink.content.contains(keyword) |
                MagnetLink.images.contains(keyword)
            ).count()
            test_count += count
        
        return {
            "success": True,
            "data": {
                "total_records": total_count,
                "records_with_images": with_images_count,
                "test_records": test_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.delete("/api/delete/test-data")
def delete_test_data(
    confirm: bool = Query(False, description="确认删除测试数据"),
    db: Session = Depends(get_db)
):
    """删除测试数据（包含特定关键词的记录）"""
    if not confirm:
        return {
            "success": False,
            "message": "请确认删除测试数据，添加 ?confirm=true 参数",
            "data": {"deleted_count": 0}
        }
    
    try:
        # 查找测试数据（包含特定关键词的记录）
        test_keywords = ['test', '测试', 'workflow_test', 'downloaded_images_test']
        test_records = []
        
        for keyword in test_keywords:
            records = db.query(MagnetLink).filter(
                MagnetLink.title.contains(keyword) |
                MagnetLink.content.contains(keyword) |
                MagnetLink.images.contains(keyword)
            ).all()
            test_records.extend(records)
        
        # 去重
        test_records = list({record.id: record for record in test_records}.values())
        total_count = len(test_records)
        
        if total_count == 0:
            return {
                "success": True,
                "message": "没有找到测试数据",
                "data": {"deleted_count": 0}
            }
        
        deleted_images = []
        
        # 删除测试数据的图片文件
        for record in test_records:
            if record.images:
                try:
                    image_list = json.loads(record.images)
                    for image_path in image_list:
                        if os.path.exists(image_path) and image_path.startswith(('downloaded_images', 'workflow_test_images')):
                            try:
                                os.remove(image_path)
                                deleted_images.append(image_path)
                            except Exception as e:
                                print(f"删除图片文件失败 {image_path}: {e}")
                except json.JSONDecodeError:
                    pass
            
            # 删除数据库记录
            db.delete(record)
        
        db.commit()
        
        # 清除仪表盘缓存
        clear_dashboard_cache()
        
        # 记录日志
        emit_log("INFO", f"删除测试数据，共 {total_count} 条", "delete", {
            "deleted_count": total_count,
            "deleted_ids": [r.id for r in test_records],
            "deleted_images": len(deleted_images)
        })
        
        return {
            "success": True,
            "message": f"成功删除 {total_count} 条测试数据",
            "data": {
                "deleted_count": total_count,
                "deleted_ids": [r.id for r in test_records],
                "deleted_images": deleted_images
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除测试数据失败: {str(e)}")

@router.delete("/api/delete/all")
def delete_all_records(
    confirm: bool = Query(False, description="确认删除所有记录"),
    db: Session = Depends(get_db)
):
    """删除所有记录"""
    if not confirm:
        return {
            "success": False,
            "message": "请确认删除所有记录，添加 ?confirm=true 参数",
            "data": {"deleted_count": 0}
        }
    
    try:
        # 获取所有记录
        all_records = db.query(MagnetLink).all()
        total_count = len(all_records)
        
        if total_count == 0:
            return {
                "success": True,
                "message": "数据库中没有记录",
                "data": {"deleted_count": 0}
            }
        
        deleted_images = []
        
        # 删除所有关联的图片文件
        for record in all_records:
            if record.images:
                try:
                    image_list = json.loads(record.images)
                    for image_path in image_list:
                        if os.path.exists(image_path) and image_path.startswith(('downloaded_images', 'workflow_test_images')):
                            try:
                                os.remove(image_path)
                                deleted_images.append(image_path)
                            except Exception as e:
                                print(f"删除图片文件失败 {image_path}: {e}")
                except json.JSONDecodeError:
                    pass
        
        # 删除所有数据库记录
        db.query(MagnetLink).delete()
        db.commit()
        
        # 清除仪表盘缓存
        clear_dashboard_cache()
        
        # 记录日志
        emit_log("WARNING", f"删除所有记录，共 {total_count} 条", "delete", {
            "deleted_count": total_count,
            "deleted_images": len(deleted_images)
        })
        
        return {
            "success": True,
            "message": f"成功删除所有 {total_count} 条记录",
            "data": {
                "deleted_count": total_count,
                "deleted_images": deleted_images
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除所有记录失败: {str(e)}")

@router.delete("/api/delete/batch")
def delete_batch_records(
    record_ids: List[int] = Query([], description="要删除的记录ID列表"),
    db: Session = Depends(get_db)
):
    """批量删除记录"""
    try:
        if not record_ids:
            return {
                "success": False,
                "message": "请提供要删除的记录ID，使用 ?record_ids=1&record_ids=2 参数",
                "data": {"deleted_count": 0}
            }
        
        # 查找记录
        records = db.query(MagnetLink).filter(MagnetLink.id.in_(record_ids)).all()
        if not records:
            raise HTTPException(status_code=404, detail="没有找到要删除的记录")
        
        deleted_count = 0
        deleted_images = []
        
        for record in records:
            # 删除关联的图片文件
            if record.images:
                try:
                    image_list = json.loads(record.images)
                    for image_path in image_list:
                        if os.path.exists(image_path) and image_path.startswith(('downloaded_images', 'workflow_test_images')):
                            try:
                                os.remove(image_path)
                                deleted_images.append(image_path)
                            except Exception as e:
                                print(f"删除图片文件失败 {image_path}: {e}")
                except json.JSONDecodeError:
                    pass
            
            # 删除数据库记录
            db.delete(record)
            deleted_count += 1
        
        db.commit()
        
        # 清除仪表盘缓存
        clear_dashboard_cache()
        
        # 记录日志
        emit_log("INFO", f"批量删除 {deleted_count} 条记录", "delete", {
            "deleted_count": deleted_count,
            "deleted_ids": [r.id for r in records],
            "deleted_images": len(deleted_images)
        })
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 条记录",
            "data": {
                "deleted_count": deleted_count,
                "deleted_ids": [r.id for r in records],
                "deleted_images": deleted_images
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除失败: {str(e)}")

@router.delete("/api/delete/{record_id}")
def delete_single_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    """删除单个记录"""
    try:
        # 查找记录
        record = db.query(MagnetLink).filter(MagnetLink.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        
        # 删除关联的图片文件
        deleted_images = []
        if record.images:
            try:
                image_list = json.loads(record.images)
                for image_path in image_list:
                    if os.path.exists(image_path) and image_path.startswith(('downloaded_images', 'workflow_test_images')):
                        try:
                            os.remove(image_path)
                            deleted_images.append(image_path)
                        except Exception as e:
                            print(f"删除图片文件失败 {image_path}: {e}")
            except json.JSONDecodeError:
                pass
        
        # 删除数据库记录
        db.delete(record)
        db.commit()
        
        # 清除仪表盘缓存
        clear_dashboard_cache()
        
        # 记录日志
        emit_log("INFO", f"删除记录 ID: {record_id}, 标题: {record.title[:30]}...", "delete", {
            "record_id": record_id,
            "title": record.title,
            "deleted_images": len(deleted_images)
        })
        
        return {
            "success": True,
            "message": f"成功删除记录 ID: {record_id}",
            "data": {
                "deleted_id": record_id,
                "deleted_images": deleted_images
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
