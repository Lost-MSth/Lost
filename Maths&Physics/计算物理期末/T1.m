%{
��һ�⣬��ֵ���ֺ���ֵ���
%}
function main
clc;
clear;
close all;
format long;

% ������
t_min = -2; % �����½�
t_max = -1; % �����Ͻ�
dt = (t_max - t_min) / 3 / 10000; % ��ֵ���ֲ�ּ��
func1 = @(t) exp(2 .* t) ./ (1 - exp(t)); % �����������
x_start = -5; % ��ʼ������
h = 0.1; % ��������
n = 3; % �����ĸ��ĸ���


% ����
% ��ֵ����
s = simpson38_integral(func1, t_min, t_max, dt);


func2 = @(x) x^3 + 2 * x^2 - 12 * x - s; % ���ⷽ�̾��

% ��ֵ�����������
x = x_start;
for i = 1:n
    x_root = get_root(func2, x, h);
    fprintf('��%d����Ϊ��%g\n', i, x_root);
    x = x_root + h; % ��һ����ʼ��
end


function s = simpson38_integral(func, a, b, h)
    %{
    Simpson3/8��ֵ���ֺ���
    IN: func �������
        a ��������
        b ��������
        h ��ּ��
    OUT: s ����ֵ
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
        �������
        �������Ӷ��ַ�
        IN: f �������
            x0 ������ʼ��
            h ��������
            delta=10e-7 Ҫ�����
        OUT: x_root ��
    %}
    if nargin < 4       
        delta = 10^-8;  % ����׼
    end
    n_max = 10^8;  % �����������
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
        error('���������������')
    end
    x_root = x0;
