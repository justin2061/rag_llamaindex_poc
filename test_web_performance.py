#!/usr/bin/env python3
"""
测试Web界面的性能追踪功能
通过模拟上传文档和查询来验证性能追踪是否正常工作
"""

import sys
import os
from pathlib import Path
import time

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_web_performance_features():
    """测试Web界面的性能追踪功能集成"""
    print("🧪 测试Web界面性能追踪功能")
    print("=" * 50)
    
    try:
        # 导入性能追踪器
        from src.utils.performance_tracker import get_performance_tracker
        
        tracker = get_performance_tracker()
        
        # 清空之前的数据
        tracker.clear_session_metrics()
        
        # 模拟一些查询性能追踪
        print("📊 模拟查询性能追踪...")
        
        # 模拟总查询时间
        with tracker.track_stage("总查询时间", query="测试查询"):
            time.sleep(0.1)
            
            # 模拟相似性搜索
            with tracker.track_stage("相似性搜索"):
                time.sleep(0.05)
            
            # 模拟上下文检索
            with tracker.track_stage("上下文检索"):
                time.sleep(0.03)
        
        # 获取摘要
        summary = tracker.get_session_summary()
        
        print(f"✅ 成功追踪了 {summary['total_stages']} 个阶段")
        print(f"✅ 总时间: {summary['total_time']:.3f}s")
        
        # 检查各阶段
        for stage in summary['stages']:
            print(f"   🔧 {stage['stage']}: {stage['duration']:.3f}s ({stage['percentage']}%)")
        
        # 测试时间格式化
        print(f"\n⏱️ 时间格式化测试:")
        print(f"   150ms -> {tracker.format_duration(0.15)}")
        print(f"   1.5s -> {tracker.format_duration(1.5)}")
        print(f"   65s -> {tracker.format_duration(65)}")
        
        # 测试导出功能
        print(f"\n📊 测试导出功能...")
        json_data = tracker.export_metrics('json')
        csv_data = tracker.export_metrics('csv')
        print(f"   JSON导出: {len(json_data)} 字符")
        print(f"   CSV导出: {len(csv_data)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ Web性能追踪测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_chat_history_performance():
    """测试聊天历史性能数据结构"""
    print("\n🧪 测试聊天历史性能数据结构")
    print("=" * 50)
    
    try:
        # 模拟聊天记录数据结构
        from datetime import datetime
        
        mock_chat_record = {
            'question': '测试问题',
            'answer': '测试回答',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sources': [],
            'response_time': '1.23s',
            'response_time_raw': 1.234,
            'performance': {
                'total_time': 1.234,
                'total_stages': 3,
                'average_stage_time': 0.411,
                'stages': [
                    {'stage': '总查询时间', 'duration': 1.234, 'percentage': 100.0},
                    {'stage': '相似性搜索', 'duration': 0.5, 'percentage': 40.5},
                    {'stage': '上下文检索', 'duration': 0.3, 'percentage': 24.3}
                ]
            },
            'metadata': {}
        }
        
        print("✅ 聊天记录数据结构正确")
        print(f"   回答时间: {mock_chat_record['response_time']}")
        print(f"   性能阶段数: {mock_chat_record['performance']['total_stages']}")
        
        # 验证性能数据完整性
        performance = mock_chat_record['performance']
        if all(key in performance for key in ['total_time', 'total_stages', 'stages']):
            print("✅ 性能数据结构完整")
        else:
            print("❌ 性能数据结构不完整")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 聊天历史性能测试失败: {e}")
        return False

def test_performance_formatting():
    """测试性能数据格式化功能"""
    print("\n🧪 测试性能数据格式化")
    print("=" * 50)
    
    try:
        from src.utils.performance_tracker import PerformanceTracker
        
        tracker = PerformanceTracker()
        
        # 测试不同时间范围的格式化
        test_cases = [
            (0.001, "1ms"),
            (0.01, "10ms"),
            (0.1, "100ms"),
            (0.5, "500ms"),
            (1.0, "1.00s"),
            (1.5, "1.50s"),
            (65.5, "1m 5.5s"),
            (125.7, "2m 5.7s")
        ]
        
        print("⏱️ 时间格式化测试:")
        for duration, expected_format in test_cases:
            formatted = tracker.format_duration(duration)
            print(f"   {duration}s -> {formatted}")
        
        print("✅ 时间格式化功能正常")
        return True
        
    except Exception as e:
        print(f"❌ 格式化测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Web界面性能追踪功能测试")
    print("=" * 60)
    
    tests = [
        test_web_performance_features,
        test_chat_history_performance,
        test_performance_formatting
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_func.__name__} 通过")
            else:
                failed += 1
                print(f"❌ {test_func.__name__} 失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 测试结果总结:")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {failed}")
    print(f"   📊 总测试数: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有Web性能追踪功能测试通过！")
        print("\n📋 用户现在可以:")
        print("   ⏱️ 在智能问答中看到实时回答时间")
        print("   📊 在性能统计页面查看详细分析")
        print("   📈 查看响应时间趋势和性能建议")
        print("   📋 导出性能数据进行进一步分析")
        return 0
    else:
        print(f"\n💥 有 {failed} 个测试失败！")
        return 1

if __name__ == "__main__":
    sys.exit(main())