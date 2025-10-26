"""
路径测试脚本 - 用于验证静态文件路径配置
"""
from pathlib import Path
from config import config

def test_paths():
    """测试路径配置"""
    print("=" * 60)
    print("📂 路径配置测试")
    print("=" * 60)
    
    # 1. 项目根目录
    print(f"\n🏠 项目根目录:")
    print(f"   {config.ROOT}")
    print(f"   存在: {'✅' if config.ROOT.exists() else '❌'}")
    
    # 2. Static 目录
    print(f"\n📁 Static 目录:")
    print(f"   {config.static_path}")
    print(f"   存在: {'✅' if config.static_path.exists() else '❌'}")
    
    # 3. Static/images 目录
    static_images = config.static_path / 'images'
    print(f"\n🖼️  Static/images 目录:")
    print(f"   {static_images}")
    print(f"   存在: {'✅' if static_images.exists() else '❌'}")
    if not static_images.exists():
        print(f"   ⚠️  需要创建: {static_images}")
        static_images.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 已创建")
    
    # 4. Static/images/original 目录
    original_dir = config.static_path / 'images' / 'original'
    print(f"\n📷 Static/images/original 目录:")
    print(f"   {original_dir}")
    print(f"   存在: {'✅' if original_dir.exists() else '❌'}")
    if not original_dir.exists():
        print(f"   ⚠️  需要创建: {original_dir}")
        original_dir.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ 已创建")
    
    # 5. 测试文件路径
    test_filename = "test_20241026_12345678.jpg"
    test_path = original_dir / test_filename
    print(f"\n🧪 测试文件路径:")
    print(f"   完整路径: {test_path}")
    
    # 6. 相对路径
    relative_path = test_path.relative_to(config.static_path)
    print(f"\n🔗 相对路径:")
    print(f"   原始: {relative_path}")
    print(f"   字符串: {str(relative_path)}")
    
    # 7. URL路径（修复反斜杠）
    url_path = str(relative_path).replace('\\', '/')
    print(f"\n🌐 URL路径:")
    print(f"   修复后: {url_path}")
    print(f"   完整URL: /static/{url_path}")
    
    # 8. Flask配置
    print(f"\n⚙️  Flask配置:")
    print(f"   static_folder: {config.app.static_folder}")
    print(f"   results_url_prefix: {config.app.results_url_prefix}")
    
    # 9. 上传目录
    print(f"\n📤 上传目录:")
    print(f"   {config.uploads_path}")
    print(f"   存在: {'✅' if config.uploads_path.exists() else '❌'}")
    
    # 10. 结果目录
    print(f"\n📊 结果目录:")
    print(f"   {config.results_path}")
    print(f"   存在: {'✅' if config.results_path.exists() else '❌'}")
    
    print("\n" + "=" * 60)
    print("✅ 路径测试完成")
    print("=" * 60)
    
    # 返回测试结果
    return {
        'root_exists': config.ROOT.exists(),
        'static_exists': config.static_path.exists(),
        'static_images_exists': static_images.exists(),
        'original_dir_exists': original_dir.exists(),
        'test_url': f"/static/{url_path}"
    }

if __name__ == "__main__":
    results = test_paths()
    
    # 检查是否所有目录都存在
    if all([
        results['root_exists'],
        results['static_exists'],
        results['static_images_exists'],
        results['original_dir_exists']
    ]):
        print("\n🎉 所有目录配置正确！")
        print(f"\n💡 测试URL示例: {results['test_url']}")
    else:
        print("\n⚠️  某些目录不存在，请检查配置")

