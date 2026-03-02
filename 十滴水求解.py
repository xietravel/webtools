import heapq
import time
import math
from collections import deque

ROWS, COLS = 6, 6
DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

# 增加时间限制和节点限制
TIME_LIMIT = 360.0  # 增加到10分钟
MAX_NODES = 6_000_000  # 增加到1000万节点

# ----------- 输入布局解析函数 -----------
def parse_board_from_string(s):
    lines = s.strip().split("\n")
    board = []
    for line in lines:
        row = [int(x) for x in line.strip().split()]
        board.append(row)
    return board

def get_board_and_moves_from_input():
    print("请输入棋盘布局，每行6个数字，用空格分隔，共6行：")
    lines = []
    for _ in range(ROWS):
        line = input()
        lines.append(line)
    user_input = "\n".join(lines)
    board = parse_board_from_string(user_input)

    moves = int(input("请输入 INITIAL_MOVES (初始步数): "))
    return board, moves

# ----------- 压缩与解压 -----------
def board_to_int(board):
    val = 0
    shift = 0
    for r in range(ROWS):
        for c in range(COLS):
            val |= (board[r][c] & 0b111) << shift
            shift += 3
    return val

def int_to_board(val):
    board = [[0]*COLS for _ in range(ROWS)]
    shift = 0
    for r in range(ROWS):
        for c in range(COLS):
            board[r][c] = (val >> shift) & 0b111
            shift += 3
    return board

def is_empty_int(val):
    return val == 0

def pretty_print_board(board):
    return "\n".join(" ".join(str(v) for v in row) for row in board)

# ----------- 修复版的波处理函数 -----------
def simulate_add_wave_detailed(val, r, c, debug=False):
    """修复：正确处理多个爆炸源影响同一格子的情况"""
    board = int_to_board(val)
    eliminated = 0
    
    if debug:
        print(f"\n=== 开始模拟: 位置({r+1},{c+1}), 原值={board[r][c]} ===")
        print("初始棋盘:")
        print(pretty_print_board(board))
    
    if board[r][c] == 0:
        board[r][c] = 1
        if debug:
            print(f"空位加水，变为1")
        return board_to_int(board), eliminated, board
        
    original_value = board[r][c]
    board[r][c] += 1
    if debug:
        print(f"加水: {original_value} -> {board[r][c]}")
    
    # 使用集合而不是队列来避免重复
    explosion_set = set()
    if board[r][c] > 4:
        explosion_set.add((r, c))
        if debug:
            print(f"触发爆炸! 加入爆炸集: ({r+1},{c+1})")
    
    wave_count = 0
    while explosion_set:
        wave_count += 1
        if debug:
            print(f"\n--- 第{wave_count}波爆炸 ---")
            print(f"爆炸格子: {[(x+1,y+1) for x,y in explosion_set]}")
        
        # 先处理所有爆炸格子的标记
        current_explosions = list(explosion_set)
        explosion_set.clear()
        
        # 先标记所有要爆炸的格子为0，并记录消除数
        for x, y in current_explosions:
            if board[x][y] <= 4:  # 可能已经被其他爆炸处理过
                continue
            if debug:
                print(f"  ({x+1},{y+1}) 爆炸: {board[x][y]} -> 0")
            board[x][y] = 0
            eliminated += 1
        
        # 修复：使用字典记录每个格子被影响的次数
        affect_counts = {}
        
        for x, y in current_explosions:
            for dr, dc in DIRS:
                nr, nc = x + dr, y + dc
                # 寻找第一个非空格子
                while 0 <= nr < ROWS and 0 <= nc < COLS:
                    # 跳过空格子和当前波次已经爆炸的格子
                    if board[nr][nc] == 0 or (nr, nc) in current_explosions:
                        nr += dr
                        nc += dc
                        continue
                    # 记录这个格子被影响
                    key = (nr, nc)
                    affect_counts[key] = affect_counts.get(key, 0) + 1
                    break
                else:
                    # 这个方向没有找到非空格子
                    if debug:
                        print(f"  ({x+1},{y+1}) -> 边界: 无影响")
        
        # 统一处理所有受影响格子的加水（考虑多次影响）
        for (nr, nc), count in affect_counts.items():
            old_value = board[nr][nc]
            board[nr][nc] += count  # 关键：加count次水，不是1次
            if debug:
                if count > 1:
                    print(f"  影响 ({nr+1},{nc+1}): {old_value} -> {board[nr][nc]} (+{count})")
                else:
                    print(f"  影响 ({nr+1},{nc+1}): {old_value} -> {board[nr][nc]}")
            if board[nr][nc] > 4:
                explosion_set.add((nr, nc))
                if debug:
                    print(f"    新爆炸点: ({nr+1},{nc+1})")
    
    if debug:
        print(f"\n最终棋盘:")
        print(pretty_print_board(board))
        print(f"总消除: {eliminated} 个格子")
        print("=== 模拟结束 ===\n")
    
    return board_to_int(board), eliminated, board

def simulate_add_wave_optimized(val, r, c):
    """修复版的优化波处理"""
    board = int_to_board(val)
    eliminated = 0
    
    if board[r][c] == 0:
        board[r][c] = 1
        return board_to_int(board), eliminated
        
    board[r][c] += 1
    
    # 使用集合避免重复
    explosion_set = set()
    if board[r][c] > 4:
        explosion_set.add((r, c))
    
    while explosion_set:
        current_explosions = list(explosion_set)
        explosion_set.clear()
        
        # 先标记爆炸
        for x, y in current_explosions:
            if board[x][y] <= 4:
                continue
            board[x][y] = 0
            eliminated += 1
        
        # 修复：记录每个格子被影响的次数
        affect_counts = {}
        for x, y in current_explosions:
            for dr, dc in DIRS:
                nr, nc = x + dr, y + dc
                while 0 <= nr < ROWS and 0 <= nc < COLS:
                    if board[nr][nc] == 0 or (nr, nc) in current_explosions:
                        nr += dr
                        nc += dc
                        continue
                    key = (nr, nc)
                    affect_counts[key] = affect_counts.get(key, 0) + 1
                    break
        
        # 统一加水（考虑多次影响）
        for (nr, nc), count in affect_counts.items():
            board[nr][nc] += count
            if board[nr][nc] > 4:
                explosion_set.add((nr, nc))
    
    return board_to_int(board), eliminated

# ----------- 验证函数 -----------
def validate_solution(start_board, path, initial_moves, debug=False):
    """完整验证解决方案"""
    if debug:
        print("\n" + "="*50)
        print("验证解决方案")
        print("="*50)
    
    current_board = [row[:] for row in start_board]
    current_moves = initial_moves
    total_eliminated = 0
    
    if debug:
        print(f"初始状态: 剩余机会={initial_moves}")
        print("初始棋盘:")
        print(pretty_print_board(current_board))
    
    for step, (r, c) in enumerate(path, 1):
        if debug:
            print(f"\n--- 步骤 {step} ---")
            print(f"操作: 在({r+1},{c+1})加水")
        
        # 检查剩余机会
        if current_moves <= 0:
            if debug:
                print(f"❌ 错误: 剩余机会为{current_moves}，不能执行操作!")
            return False, current_moves
        
        # 执行操作
        current_val = board_to_int(current_board)
        new_val, elim, new_board = simulate_add_wave_detailed(current_val, r, c, debug=debug)
        extra = elim // 3
        new_moves = current_moves - 1 + extra
        total_eliminated += elim
        
        if debug:
            print(f"结果: 消除{elim}格, 获得额外机会+{extra}, 剩余机会{new_moves}")
        
        current_board = new_board
        current_moves = new_moves
    
    # 最终检查
    final_val = board_to_int(current_board)
    is_solved = is_empty_int(final_val)
    
    if debug:
        print("\n" + "="*50)
        print("验证结果总结")
        print("="*50)
        
        if is_solved:
            print("✅ 成功清空棋盘!")
        else:
            print("❌ 棋盘未清空!")
            print("最终棋盘:")
            print(pretty_print_board(current_board))
            return False, current_moves
        
        print(f"总步数: {len(path)}")
        print(f"总消除格子: {total_eliminated}")
        print(f"最终剩余机会: {current_moves}")
        
        print("\n✅ 解决方案验证通过!")
    
    return is_solved, current_moves

# ----------- 改进的启发式函数 -----------
def heuristic_improved(val, moves_left, depth):
    """改进的启发式函数，考虑深度和剩余步数"""
    board = int_to_board(val)
    
    if is_empty_int(val):
        return moves_left * 1000  # 空棋盘给极高评分
    
    # 计算各种指标
    non_zero = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] > 0)
    total_water = sum(board[r][c] for r in range(ROWS) for c in range(COLS))
    
    # 爆炸潜力
    explosion_potential = 0
    critical_count = 0
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] >= 4:
                critical_count += 2
                explosion_potential += 10
            elif board[r][c] == 3:
                critical_count += 1
                explosion_potential += 5
    
    # 估计需要的步数
    estimated_required = max(1, non_zero * 0.7 - critical_count * 0.3)
    
    # 评分 = 剩余步数 * 100 + 爆炸潜力 - 估计需要的步数 - 深度惩罚
    score = moves_left * 100 + explosion_potential - estimated_required * 10 - depth * 0.1
    
    return score

# ----------- 智能移动选择 -----------
def get_promising_moves_improved(val, moves_left, depth):
    """改进的移动选择，考虑长期收益"""
    board = int_to_board(val)
    moves = []
    
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 0:
                continue
                
            priority = 0
            
            # 基础价值
            priority += board[r][c] * 5
            
            # 立即爆炸潜力（高优先级）
            if board[r][c] >= 4:
                priority += 30
            elif board[r][c] == 3:
                priority += 15
            
            # 模拟这一步的效果（使用优化版本，因为只是估算）
            new_val, elim = simulate_add_wave_optimized(val, r, c)
            extra = elim // 3
            
            # 连锁反应奖励
            priority += elim * 2
            priority += extra * 20  # 额外步数奖励
            
            # 位置奖励（中心区域）
            center_distance = abs(r - 2.5) + abs(c - 2.5)
            priority += (6 - center_distance)
            
            # 深度惩罚：越深越鼓励选择高回报的移动
            if depth > 10:
                priority *= (1 - depth * 0.01)
            
            moves.append((priority, r, c))
    
    # 按优先级排序
    moves.sort(reverse=True)
    
    # 动态调整候选数量
    base_candidates = 8
    if moves_left > 10:
        base_candidates = 12
    if depth > 15:
        base_candidates = 6
    
    return [(r, c) for _, r, c in moves[:base_candidates]]

# ----------- 改进的A*搜索（渐进式搜索） -----------
def progressive_astar_search(start_board, initial_moves):
    """渐进式A*搜索：先快速找可行解，再逐步优化"""
    start_time = time.time()
    start_val = board_to_int(start_board)
    
    if is_empty_int(start_val):
        return initial_moves, [], 0, False
    
    print("开始渐进式搜索...")
    
    # 阶段1：快速找到第一个解（时间限制：20%）
    print("阶段1: 快速搜索可行解...")
    phase1_time = TIME_LIMIT * 0.2
    best_solution = None
    
    # 初始搜索
    open_set = []
    h0 = heuristic_improved(start_val, initial_moves, 0)
    heapq.heappush(open_set, (-h0, 0, initial_moves, start_val, []))  # 最大堆
    
    visited = {}
    nodes_expanded = 0
    phase_start = time.time()
    
    while open_set and time.time() - phase_start < phase1_time:
        neg_score, depth, moves_left, val, path = heapq.heappop(open_set)
        nodes_expanded += 1
        
        # 找到解
        if is_empty_int(val):
            is_valid, final_moves = validate_solution(start_board, path, initial_moves, debug=False)
            if is_valid:
                best_solution = (final_moves, path, nodes_expanded)
                print(f"阶段1找到解: 剩余步数={final_moves}, 使用步数={len(path)}")
                break
        
        # 状态剪枝
        state_key = (val, moves_left)
        if state_key in visited and visited[state_key] <= depth:
            continue
        visited[state_key] = depth
        
        if moves_left <= 0:
            continue
        
        # 获取移动
        candidates = get_promising_moves_improved(val, moves_left, depth)
        
        for r, c in candidates:
            new_val, elim = simulate_add_wave_optimized(val, r, c)
            extra = elim // 3
            new_moves = moves_left - 1 + extra
            
            if new_moves < 0:
                continue
                
            new_depth = depth + 1
            new_path = path + [(r, c)]
            
            h = heuristic_improved(new_val, new_moves, new_depth)
            heapq.heappush(open_set, (-h, new_depth, new_moves, new_val, new_path))
    
    # 阶段2：如果找到解，继续优化（时间限制：80%）
    if best_solution:
        print("阶段2: 优化现有解...")
        best_final_moves, best_path, _ = best_solution
        
        # 重新初始化搜索，但保留当前最佳解
        open_set = []
        visited = {}
        
        # 添加初始状态
        h0 = heuristic_improved(start_val, initial_moves, 0)
        heapq.heappush(open_set, (-h0, 0, initial_moves, start_val, []))
        
        phase_start = time.time()
        improvement_count = 0
        
        while open_set and time.time() - start_time < TIME_LIMIT:
            neg_score, depth, moves_left, val, path = heapq.heappop(open_set)
            nodes_expanded += 1
            
            # 定期输出进度
            if nodes_expanded % 100000 == 0:
                elapsed = time.time() - start_time
                print(f"进度: {elapsed:.1f}s, 节点: {nodes_expanded}, 最佳解: {best_final_moves}步")
            
            # 找到解
            if is_empty_int(val):
                is_valid, final_moves = validate_solution(start_board, path, initial_moves, debug=False)
                if is_valid and final_moves > best_final_moves:
                    best_final_moves = final_moves
                    best_path = path
                    improvement_count += 1
                    print(f"找到更好解 #{improvement_count}: 剩余步数={final_moves} (+{final_moves-best_final_moves})")
            
            # 剪枝：如果当前状态的最大可能剩余步数不如最佳解，剪枝
            max_possible = moves_left + (36 - depth) // 2  # 乐观估计
            if max_possible <= best_final_moves:
                continue
            
            # 状态剪枝
            state_key = (val, moves_left)
            if state_key in visited and visited[state_key] <= depth:
                continue
            visited[state_key] = depth
            
            if moves_left <= 0:
                continue
            
            # 获取移动
            candidates = get_promising_moves_improved(val, moves_left, depth)
            
            for r, c in candidates:
                new_val, elim = simulate_add_wave_optimized(val, r, c)
                extra = elim // 3
                new_moves = moves_left - 1 + extra
                
                if new_moves < 0:
                    continue
                    
                new_depth = depth + 1
                new_path = path + [(r, c)]
                
                # 乐观剪枝：如果新状态的最大可能不如最佳解，跳过
                new_max_possible = new_moves + (36 - new_depth) // 2
                if new_max_possible <= best_final_moves:
                    continue
                
                h = heuristic_improved(new_val, new_moves, new_depth)
                heapq.heappush(open_set, (-h, new_depth, new_moves, new_val, new_path))
        
        print(f"优化完成，找到{improvement_count}个改进解")
        return best_final_moves, best_path, nodes_expanded, False
    
    return None, None, nodes_expanded, True

# ----------- 主搜索函数 -----------
def smart_solve_with_long_running(start_board, initial_moves):
    """长时间运行的智能求解器"""
    print(f"开始长时间搜索（最长{TIME_LIMIT/60:.1f}分钟）...")
    
    final_moves, path, nodes, timed_out = progressive_astar_search(start_board, initial_moves)
    
    if final_moves is not None and path:
        print(f"\n🎯 搜索完成!")
        print(f"最终剩余步数: {final_moves}")
        print(f"使用步数: {len(path)}")
        print(f"净收益: {final_moves - initial_moves} 步")
        print(f"扩展节点数: {nodes}")
        
        # 验证解决方案
        print("\n验证最终解决方案...")
        is_valid, actual_final_moves = validate_solution(start_board, path, initial_moves, debug=True)
        
        if is_valid:
            print(f"✅ 验证通过! 实际最终剩余步数: {actual_final_moves}")
        else:
            print("❌ 验证失败!")
            
        return final_moves, path, nodes, timed_out, is_valid
    else:
        print("未找到解或搜索超时")
        return None, None, nodes, timed_out, False

# ----------- 主程序 -----------
if __name__ == "__main__":
    while True:
        try:
            print("="*60)
            print(f"长时间搜索模式（最长{TIME_LIMIT/60:.1f}分钟）")
            print("="*60)
            
            START_BOARD, INITIAL_MOVES = get_board_and_moves_from_input()
            
            start_time = time.time()
            final_moves, path, nodes, timed_out, is_valid = smart_solve_with_long_running(START_BOARD, INITIAL_MOVES)
            
            total_time = time.time() - start_time
            print(f"\n总搜索时间: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")
            
            if final_moves is not None and path and is_valid:
                print(f"\n最终结果:")
                print(f"初始步数: {INITIAL_MOVES}")
                print(f"使用步数: {len(path)}")
                print(f"最终剩余步数: {final_moves}")
                print(f"净收益: {final_moves - INITIAL_MOVES} 步")
                print("操作序列:", " → ".join([f"({r+1},{c+1})" for r, c in path]))
            
            # 是否继续
            cont = input("\n是否继续输入新的棋盘？(y/n): ").strip().lower()
            if cont != "y":
                print("谢谢使用！再见！")
                break
                
        except KeyboardInterrupt:
            print("\n用户中断程序")
            print("正在保存当前最佳解...")
            break
        except Exception as e:
            print(f"发生错误: {e}")
            import traceback
            traceback.print_exc()
            print("请重新输入")
