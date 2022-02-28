%{
�����⣬��΢�ַ��̱���ֵ����
���ô�з���ϼ��������Ͷ��ַ����
%}
function main
clc;
clear;
close all;
format long;


% ȫ�ֳ�����
e = 10^-10; % ����׼
N = 10000; % �ָ����
a = 0; % ��߽�
b = pi; % �ұ߽�
alpha = 0; % ��߽��޶�ֵ
beta = 0; % �ұ߽��޶�ֵ
lambda_0 = -1; % ����ֵ������ʼ��
delta_lambda = 1; % ����ֵ��������
n = 5; % ����ֵ��������



t = a: (b - a) / N: b; % �Ա���ɢ�л�
j = 0;
x = lambda_0;
% Ԥ����
func = @(t, y) [y(2), - (x/2 - 5 * sin(5 * t)) * y(1)]; % ���������
z = runge_kutta_4(func, t, [10, alpha]);
r2 = beta - z(end, 2);
% �������Ӷ��ַ�
while j < n
    r1 = r2;
    x = x + delta_lambda;
    func = @(t, y) [y(2), - (x/2 - 5 * sin(5 * t)) * y(1)]; % ���������
    z = runge_kutta_4(func, t, [10, alpha]);
    r2 = beta - z(end, 2);
    
    if r1 * r2 < 0
        % ��������
        s0 = x - delta_lambda; % ��߱���ֵ
        s1 = x; % �ұ߱���ֵ
        r_left = r1;
        r_right = r2;
        % û��untilѭ��������һ������
        m = (s0 + s1) / 2;
        func = @(t, y) [y(2), - (m/2 - 5 * sin(5 * t)) * y(1)]; % ���������
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
            func = @(t, y) [y(2), - (m/2 - 5 * sin(5 * t)) * y(1)]; % ���������
            z = runge_kutta_4(func, t, [10, alpha]);
        end
        % ������
        j = j + 1;
        fprintf('��%d������ֵΪ��%g\n', j, m);
        figure;
        plot(t, z(:, 2));
        title('��' + string(j) + '������ֵ�ı�������');
    end
end


function z = runge_kutta_4(f, t, z0)
    %{
        �Ľ�Runge-Kutta��
        IN: f �������������
            t �Ա�������
            z0 ��ʼֵ
        OUT: z �����һ�д���һ������
    %}
    n = length(t); % ά��
    h = t(2) - t(1); % �Ա������
    z(1, :) = z0;
    for i = 1:n-1
        k1 = f(t(i), z(i,:));
        k2 = f(t(i) + 0.5 * h, z(i,:) + h * k1 / 2);
        k3 = f(t(i) + 0.5 * h, z(i,:) + h * k2 / 2);
        k4 = f(t(i) + h, z(i,:) + h * k3);
        z(i + 1, :) = z(i, :) + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6;
    end