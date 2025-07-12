#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faucet模板 - 通用水龙头请求工具
支持配置化、代理、验证码自动处理
"""

import json
import os
import random
import time
import requests
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha
from typing import Optional, Dict, Any, List
import logging


class FaucetTemplate:
    def __init__(self, config_file: str = "config.json"):
        """
        初始化Faucet模板
        
        Args:
            config_file: 配置文件路径
        """
        # 获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 加载环境变量
        load_dotenv()
        
        # 加载配置
        self.config = self._load_config(config_file)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化2captcha
        self.solver = TwoCaptcha(os.getenv('TWOCAPTCHA_API_KEY'))
        
        # 加载代理
        self.proxies = self._load_proxies()
        
        # 当前代理索引
        self.current_proxy_index = 0
        
        # 初始化User-Agent列表
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # 初始化requests会话
        self.session = requests.Session()
        
        # 设置请求头
        if 'headers' in self.config:
            self.session.headers.update(self.config['headers'])
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """加载配置文件"""
        # 确保使用正确的文件路径
        if not os.path.isabs(config_file):
            config_file = os.path.join(self.script_dir, config_file)
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件 {config_file} 未找到")
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {config_file} 格式错误")
    
    def _load_proxies(self) -> List[Dict[str, str]]:
        """加载代理配置"""
        proxies = []
        proxy_file = os.path.join(os.path.dirname(self.script_dir), "proxy.txt")
        
        if not os.path.exists(proxy_file):
            self.logger.info("代理文件不存在，将不使用代理")
            return proxies
        
        try:
            with open(proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxy_dict = self._parse_proxy(line)
                        if proxy_dict:
                            proxies.append(proxy_dict)
            
            self.logger.info(f"加载了 {len(proxies)} 个代理")
            return proxies
        except Exception as e:
            self.logger.error(f"加载代理文件失败: {e}")
            return proxies
    
    def _parse_proxy(self, proxy_string: str) -> Optional[Dict[str, str]]:
        """解析代理字符串"""
        try:
            if proxy_string.startswith('http://'):
                return {'http': proxy_string, 'https': proxy_string}
            elif proxy_string.startswith('socks5://'):
                return {'http': proxy_string, 'https': proxy_string}
            else:
                return None
        except Exception as e:
            self.logger.error(f"解析代理失败: {proxy_string}, 错误: {e}")
            return None
    
    def _setup_logging(self):
        """设置日志"""
        debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        log_level = logging.DEBUG if debug_mode else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.get('log_file', 'faucet.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _solve_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """
        解决reCAPTCHA验证码
        
        Args:
            site_key: 站点密钥
            page_url: 页面URL
            
        Returns:
            验证码响应token
        """
        try:
            self.logger.info("开始解决reCAPTCHA验证码...")
            
            result = self.solver.recaptcha(
                sitekey=site_key,
                url=page_url
            )
            
            if result and 'code' in result:
                self.logger.info("reCAPTCHA验证码解决成功")
                return result['code']
            else:
                self.logger.error("reCAPTCHA验证码解决失败")
                return None
                
        except Exception as e:
            self.logger.error(f"解决reCAPTCHA验证码时发生错误: {e}")
            return None
    
    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """随机获取一个代理（已废弃）"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def _get_next_proxy(self) -> Optional[Dict[str, str]]:
        """按顺序获取下一个代理"""
        if not self.proxies:
            return None
        
        # 获取当前代理
        proxy = self.proxies[self.current_proxy_index]
        
        # 更新索引，循环使用代理列表
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        return proxy
    
    def _get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(self.user_agents)
    
    def _make_request(self, address: str, proxy: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        发送faucet请求
        
        Args:
            address: 地址
            proxy: 代理配置
            
        Returns:
            响应对象
        """
        # 准备请求数据
        data = {
            self.config['address_key']: address
        }
        
        # 添加额外参数
        if 'additional_params' in self.config:
            data.update(self.config['additional_params'])
        
        # 解决验证码
        if 'recaptcha_site_key' in self.config:
            recaptcha_token = self._solve_recaptcha(
                self.config['recaptcha_site_key'],
                self.config['url']
            )
            if recaptcha_token:
                data[self.config['recaptcha_key']] = recaptcha_token
            else:
                raise Exception("验证码解决失败")
        
        # 设置随机User-Agent
        random_ua = self._get_random_user_agent()
        self.session.headers.update({'User-Agent': random_ua})
        self.logger.info(f"使用User-Agent: {random_ua}")
        
        # 发送请求
        timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
        
        if self.config['method'].upper() == 'POST':
            response = self.session.post(
                self.config['url'],
                data=data,
                proxies=proxy,
                timeout=timeout
            )
        else:
            response = self.session.get(
                self.config['url'],
                params=data,
                proxies=proxy,
                timeout=timeout
            )
        
        return response
    
    def _check_response(self, response: requests.Response) -> tuple[bool, str]:
        """
        检查响应结果
        
        Args:
            response: 响应对象
            
        Returns:
            (是否成功, 消息)
        """
        try:
            # 检查状态码
            if response.status_code != 200:
                return False, f"HTTP错误: {response.status_code}"
            
            # 检查响应内容
            response_text = response.text
            self.logger.info(f"响应内容: {response_text}")
            
            # 尝试解析JSON响应
            try:
                json_response = response.json()
                # 如果响应是JSON格式，检查success字段
                if 'success' in json_response:
                    if json_response['success'] is True:
                        return True, "请求成功"
                    else:
                        # success为false时，尝试获取错误信息
                        error_msg = json_response.get('error', json_response.get('message', '请求失败'))
                        return False, f"请求失败: {error_msg}"
            except (ValueError, TypeError):
                # 如果不是JSON格式，继续使用原有的文本匹配逻辑
                pass
            
            response_text_lower = response_text.lower()
            
            # 检查错误指示符（优先检查错误）
            if 'error_indicators' in self.config:
                for indicator in self.config['error_indicators']:
                    if indicator.lower() in response_text_lower:
                        return False, f"请求失败: {indicator}"
            
            # 检查成功指示符
            if 'success_indicators' in self.config:
                for indicator in self.config['success_indicators']:
                    if indicator.lower() in response_text_lower:
                        return True, "请求成功"
            
            # 默认判断
            return True, "请求完成"
            
        except Exception as e:
            return False, f"响应解析错误: {e}"
    
    def claim(self, address: str, use_proxy: bool = False) -> tuple[bool, str]:
        """
        执行faucet请求
        
        Args:
            address: 钱包地址
            use_proxy: 是否使用代理
            
        Returns:
            (是否成功, 消息)
        """
        max_retries = self.config.get('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"开始第 {attempt + 1} 次尝试...")
                
                # 选择代理
                proxy = None
                if use_proxy:
                    proxy = self._get_next_proxy()
                    if proxy:
                        self.logger.info(f"使用代理: {list(proxy.values())[0]}")
                
                # 发送请求
                response = self._make_request(address, proxy)
                
                # 输出请求结果
                self.logger.info(f"请求URL: {response.url}")
                self.logger.info(f"状态码: {response.status_code}")
                self.logger.info(f"响应头: {response.headers}")
                
                # 检查响应
                success, message = self._check_response(response)
                
                if success:
                    self.logger.info(f"请求成功: {message}")
                    return True, message
                else:
                    self.logger.warning(f"请求失败: {message}")
                    if attempt < max_retries - 1:
                        self.logger.info(f"等待 {self.config.get('retry_delay', 10)} 秒后重试...")
                        time.sleep(self.config.get('retry_delay', 10))
                    
            except Exception as e:
                self.logger.error(f"请求发生错误: {e}")
                if attempt < max_retries - 1:
                    self.logger.info(f"等待 {self.config.get('retry_delay', 10)} 秒后重试...")
                    time.sleep(self.config.get('retry_delay', 10))
        
        return False, "所有尝试均失败"


def load_wallet_addresses(wallet_file: str = "wallet.txt") -> List[str]:
    """
    从wallet.txt文件加载钱包地址
    
    Args:
        wallet_file: 钱包文件路径
        
    Returns:
        钱包地址列表
    """
    addresses = []
    
    # 确保使用正确的文件路径
    if not os.path.isabs(wallet_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        wallet_file = os.path.join(script_dir, wallet_file)
    
    if not os.path.exists(wallet_file):
        print(f"❌ 钱包文件 {wallet_file} 不存在")
        return addresses
    
    try:
        with open(wallet_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    addresses.append(line)
        
        print(f"✅ 从 {wallet_file} 加载了 {len(addresses)} 个地址")
        return addresses
        
    except Exception as e:
        print(f"❌ 加载钱包文件失败: {e}")
        return addresses


def main():
    """主函数"""
    # 创建faucet实例
    faucet = FaucetTemplate()
    
    # 加载钱包地址
    addresses = load_wallet_addresses()
    
    if not addresses:
        print("❌ 没有找到有效的钱包地址")
        return
    
    print(f"🚀 开始请求faucet: {faucet.config['name']}")
    print(f"📋 共有 {len(addresses)} 个地址需要处理")
    print("="*50)
    
    # 统计结果
    success_count = 0
    failed_count = 0
    
    # 循环处理每个地址
    for i, address in enumerate(addresses, 1):
        print(f"\n[{i}/{len(addresses)}] 处理地址: {address}")
        
        # 执行请求
        success, message = faucet.claim(address, use_proxy=True)
        
        if success:
            print(f"✅ 成功: {message}")
            success_count += 1
        else:
            print(f"❌ 失败: {message}")
            failed_count += 1
        
        # 如果不是最后一个地址，等待一段时间避免请求过快
        if i < len(addresses):
            wait_time = faucet.config.get('faucet_delay', 30)
            print(f"⏱️  等待 {wait_time} 秒后处理下一个地址...")
            time.sleep(wait_time)
    
    # 输出最终统计
    print("\n" + "="*50)
    print(f"📊 处理完成统计:")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"📋 总计: {len(addresses)}")
    print(f"📈 成功率: {(success_count/len(addresses)*100):.1f}%")


if __name__ == "__main__":
    main() 