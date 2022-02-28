%{
第一题，数值积分和数值求根
%}
function main
clc;
clear;
close all;
format long;

% 常数表
t_min = -2; % 积分下界
t_max = -1; % 积分上界
dt = (t_max - t_min) / 3 / 10000; % 数值积分差分间隔
func1 = @(t) exp(2 .* t) ./ (1 - exp(t)); % 待积函数句柄
x_start = -5; % 起始搜索点
h = 0.1; % 搜索步长
n = 3; % 搜索的根的个数


% 计算
% 数值积分
s = simpson38_integral(func1, t_min, t_max, dt);


func2 = @(x) x^3 + 2 * x^2 - 12 * x - s; % 待解方程句柄

% 数值求根，逐步搜索
x = x_start;
for i = 1:n
    x_root = get_root(func2, x, h);
    fprintf('第%d个根为：%g\n', i, x_root);
    x = x_root + h; % 下一个起始点
end


function s = simpson38_integral(func, a, b, h)
    %{
    Simpson3/8数值积分函数
    IN: func 函数句柄
        a 积分下限
        b 积分上限
        h 差分间隔
    OUT: s 积分值
    %}

    if mod(b-a, h) ~= 0 || mod(floor((b-a) / h), 3) ~= 0 
        error('Wrong input');
    end

    x = a:h:b;
    y = func(x);
    s = 3 * sum(y);
    for i = 1:3:length(y)
        s = s - y(i);
    end
    s = s - y(1) - y(end);
    s = s * h * 3 / 8;
    
    
function x_root = get_root(f, x0, h, delta) 
    %{
        求根函数
        简单搜索加二分法
        IN: f 函数句柄
            x0 搜索起始点
            h 搜索步长
            delta=10e-7 要求误差
        OUT: x_root 根
    %}
    if nargin < 4       
        delta = 10^-8;  % 误差标准
    end
    n_max = 10^8;  % 最大搜索次数
    n = 0;
    
    while h > delta && n < n_max
        if f(x0 + h) * f(x0) > 0
             x0 = x0 + h;
        else
             a = x0;
             b = x0 + h;
             while abs(a - b) > delta
                x0 = (a + b) / 2;     
                if f(x0) * f(a) < 0
                    b = x0;
                else
                    a = x0;
                end
             end
             x0 = (a + b) / 2;    
             h = b - a;
        end 
        n = n + 1;
    end
    if n >= n_max
        error('超过最大搜索次数')
    end
    x_root = x0;
