%{
第三题，常微分方程本征值问题
采用打靶法结合简单搜索法和二分法求解
%}
function main
clc;
clear;
close all;
format long;


% 全局常量表
e = 10^-10; % 误差标准
N = 10000; % 分割次数
a = 0; % 左边界
b = pi; % 右边界
alpha = 0; % 左边界限定值
beta = 0; % 右边界限定值
lambda_0 = -1; % 本征值搜索起始点
delta_lambda = 1; % 本征值搜索步长
n = 5; % 本征值搜索个数



t = a: (b - a) / N: b; % 自变量散列化
j = 0;
x = lambda_0;
% 预计算
func = @(t, y) [y(2), - (x/2 - 5 * sin(5 * t)) * y(1)]; % 导函数句柄
z = runge_kutta_4(func, t, [10, alpha]);
r2 = beta - z(end, 2);
% 简单搜索加二分法
while j < n
    r1 = r2;
    x = x + delta_lambda;
    func = @(t, y) [y(2), - (x/2 - 5 * sin(5 * t)) * y(1)]; % 导函数句柄
    z = runge_kutta_4(func, t, [10, alpha]);
    r2 = beta - z(end, 2);
    
    if r1 * r2 < 0
        % 二分搜索
        s0 = x - delta_lambda; % 左边本征值
        s1 = x; % 右边本征值
        r_left = r1;
        r_right = r2;
        % 没有until循环，先做一次运算
        m = (s0 + s1) / 2;
        func = @(t, y) [y(2), - (m/2 - 5 * sin(5 * t)) * y(1)]; % 导函数句柄
        z = runge_kutta_4(func, t, [10, alpha]);
        while  abs(beta - z(end, 2)) > e
          %  fprintf('%g %g %g %g \n', m, abs(beta - z(end, 2)), s0, s1);
            if (beta - z(end, 2)) * r_left < 0
                r_right = beta - z(end, 2);
                s1 = m;
            elseif (beta - z(end, 2)) * r_right < 0
                r_left = beta - z(end, 2);
                s0 = m;
            else
                break
            end
            m = (s0 + s1) / 2;
            func = @(t, y) [y(2), - (m/2 - 5 * sin(5 * t)) * y(1)]; % 导函数句柄
            z = runge_kutta_4(func, t, [10, alpha]);
        end
        % 结果输出
        j = j + 1;
        fprintf('第%d个本征值为：%g\n', j, m);
        figure;
        plot(t, z(:, 2));
        title('第' + string(j) + '个本征值的本征函数');
    end
end


function z = runge_kutta_4(f, t, z0)
    %{
        四阶Runge-Kutta法
        IN: f 导函数句柄数组
            t 自变量数组
            z0 初始值
        OUT: z 解矩阵，一列代表一个分量
    %}
    n = length(t); % 维数
    h = t(2) - t(1); % 自变量间隔
    z(1, :) = z0;
    for i = 1:n-1
        k1 = f(t(i), z(i,:));
        k2 = f(t(i) + 0.5 * h, z(i,:) + h * k1 / 2);
        k3 = f(t(i) + 0.5 * h, z(i,:) + h * k2 / 2);
        k4 = f(t(i) + h, z(i,:) + h * k3);
        z(i + 1, :) = z(i, :) + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
    end