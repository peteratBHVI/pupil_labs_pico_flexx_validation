function [target_data_table] =  royale_LEVEL1_extract_target_data(FileName, disp_pointcloud)
%ROYALE_LEVEL1_SAMPLE3 - royale example #3:
% 

% % % %  
% """
% (*)~---------------------------------------------------------------------------
% amendments to ROYALE_LEVEL1_SAMPLE3 - royale example #3:
% author: p.wagner@unsw.edu.au / p.wagner@bhvi.org
% 
% find all target positions in point cloud of accuray recording  
%     data output: data talbe with all x y positions of all targets sorted 
% 
% dependencies:
%     - FileName == point cloud in accuracy recording folder 
%     - disp_pointcloud - visualize point cloud (very slow but looks good) 
% ---------------------------------------------------------------------------~(*)
% """
% % %   

% retrieve royale version information
royaleVersion = royale.getVersion();
fprintf('* royale version: %s\n',royaleVersion);

% open recorded file
manager = royale.CameraManager();
cameraDevice = manager.createCamera(FileName);
delete(manager);

cameraDevice.initialize();

% display some information about the connected camera
fprintf('====================================\n');
fprintf('        Camera information\n');
fprintf('====================================\n');
fprintf('Id:              %s\n',cameraDevice.getId());
fprintf('Type:            %s\n',cameraDevice.getCameraName());
fprintf('Width:           %u\n',cameraDevice.getMaxSensorWidth());
fprintf('Height:          %u\n',cameraDevice.getMaxSensorHeight());

% retrieve valid use cases
UseCases=cameraDevice.getUseCases();
fprintf('Use cases: %d\n',numel(UseCases));
fprintf('    %s\n',UseCases{:});
fprintf('====================================\n');

if (numel(UseCases) == 0)
    error('No use case available');
end

% configure playback
cameraDevice.loop(false);
cameraDevice.useTimestamps(false);

N_Frames= cameraDevice.frameCount();
fprintf('Retrieving %d frames...\n',N_Frames);

% start capture mode
cameraDevice.startCapture();

% initialize preview figure
hFig=figure('Name',...
    ['Preview: ',cameraDevice.getId(),' @ MODE_PLAYBACK'],...
    'IntegerHandle','off','NumberTitle','off');
colormap(jet(256));
TID = tic();
last_toc = toc(TID);
iFrame = 0;

% allocate variables 
data_depth_map = zeros(224, 171);
target_data_table = create_table_target_data(); 
target_data_table{N_Frames, :} = nan;

while (ishandle(hFig)) && (iFrame < N_Frames)
    % retrieve data from camera
    data = cameraDevice.getData();
    iFrame = iFrame + 1;
    
    if (mod(iFrame,10) == 0)
        this_toc=toc(TID);
        fprintf('FPS = %.2f\n',10/(this_toc-last_toc));
        last_toc=this_toc;
    end
    
    %%% notice: figures are slow.
    %%% For higher FPS (e.g. 45), do not display every frame.
    %%% e.g. by doing here:
    % if (mod(iFrame,5) ~= 0);continue;end;
    
    % prepare data, calculate distance for all data points and 
    % limit distance range  
    data_depth_map = sqrt(data.x.^2 + data.y.^2 + data.z.^2);
    data_depth_map(data_depth_map(:,:) < 0.2) = nan;
    data_depth_map(data_depth_map(:,:) > 1.7) = nan;
    
    
    new_target_data_table = find_targets(data_depth_map);
    % if no targets were found add just frame index == iFrame 
    % else add found target data 
    if isnan(target_data_table.world_cam_frame_idx(1)) 
        target_data_table = new_target_data_table;
        target_data_table.world_cam_frame_idx(1) = iFrame;
    else
        new_target_data_table.world_cam_frame_idx(1) = iFrame;
        target_data_table(iFrame, :)= new_target_data_table; 
    end
    % visualize data on demand   
    if disp_pointcloud
        set(0,'CurrentFigure',hFig);       
        my_image(data_depth_map,'depth data with found targets');
        draw_circles(new_target_data_table)
        drawnow;
    end
end

% stop capture mode
fprintf('* Stopping capture mode...\n');
cameraDevice.stopCapture();
fprintf('* ...done!\n');
close all
end

function my_image(CData,Name)
% convenience function for faster display refresh:
%  only update 'CData' on successive image calls
%  (does not update title or change resolution!)
if ~isappdata(gca,'my_imagehandle')
    my_imagehandle = imagesc(CData);
    axis image
    title(Name);
    setappdata(gca,'my_imagehandle',my_imagehandle);
else
    my_imagehandle = getappdata(gca,'my_imagehandle');
    set(my_imagehandle,'CData',CData);
end
end

% % % create datatable with sorted target info 
function [t3] = create_table_target_data()
% set up output file 
uuii = zeros(1, 34);
colNames = {'world_cam_frame_idx', ... 
            'T1_r', 'T1_x', 'T1_y', ...
            'T2_r', 'T2_x', 'T2_y', ...
            'T3_r', 'T3_x', 'T3_y', ...
            'T4_r', 'T4_x', 'T4_y', ...
            'T5_r', 'T5_x', 'T5_y', ...
            'T6_r', 'T6_x', 'T6_y', ...
            'T7_r', 'T7_x', 'T7_y', ...
            'T8_r', 'T8_x', 'T8_y', ...
            'T9_r', 'T9_x', 'T9_y', ...
            'T10_r', 'T10_x', 'T10_y', ... 
            'T11_r', 'T11_x', 'T11_y', ...
             };
t3 = array2table(uuii, 'VariableNames', colNames);
end 
% % % find each target in each q and sort to target id
function [new_table] = find_targets(data_depthmap)
% finds all targets 
[t3] = create_table_target_data();
iFrame = 1;
for t_distance = [0.28, 0.5, .7, 1, 1.45]
    depthmap = data_depthmap;
    % select data
    % % set interval for single target distant sphere 
    mean = nanmean(depthmap(depthmap(:,:) > t_distance -.1 & depthmap(:,:) < t_distance +.13));
    std  =  nanstd(depthmap(depthmap(:,:) > t_distance -.1 & depthmap(:,:) < t_distance +.13));
    
    depthmap(depthmap(:,:) < mean - 2 * std) = nan;
    depthmap(depthmap(:,:) > mean + 2 * std) = nan;
    %creat png for imfindcircles - may refine if too many false positive 
    png(:,:, 1) = depthmap;
    png(:,:, 2) = depthmap;
    png(:,:, 3) = depthmap;

    [centers, radii] = imfindcircles(png, [6 10], 'Sensitivity',0.95);
%     viscircles(centers, radii,'EdgeColor','g');
    % write to output data file radi and centre coordinates
    if ~isempty(centers)

        if t_distance == .28 && length(radii(:,1))==2
            % find smaller x value for centers 
            [~, pos] = (min(centers(:,1)));     
            t3(iFrame, 'T10_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T10_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T10_y') = num2cell(centers(pos,2));
            [~, pos] = (max(centers(:,1)));         
            t3(iFrame, 'T5_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T5_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T5_y') = num2cell(centers(pos,2));
        elseif t_distance == .28 && ~length(radii(:,1))==2
            disp("error reading .3 sphere " + string(iFrame))
        end

        if t_distance == .5 && length(radii(:,1))==3

            % find smaller x value for centers 
            [~, pos] = (min(centers(:,1)));     
            t3(iFrame, 'T9_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T9_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T9_y') = num2cell(centers(pos,2));
            [~, pos] = (max(centers(:,1)));         
            t3(iFrame, 'T8_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T8_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T8_y') = num2cell(centers(pos,2));
            [~, pos] = (min(centers(:,2)));         
            t3(iFrame, 'T6_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T6_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T6_y') = num2cell(centers(pos,2));


        elseif t_distance == .5 && ~length(radii(:,1))==3
            disp("error reading .5 sphere " + string(iFrame))
        end

        if t_distance == .7 && length(radii(:,1))==2
            % find smaller x value for centers 
            [~, pos] = (min(centers(:,1)));     
            t3(iFrame, 'T4_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T4_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T4_y') = num2cell(centers(pos,2));
            [~, pos] = (max(centers(:,1)));         
            t3(iFrame, 'T3_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T3_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T3_y') = num2cell(centers(pos,2));
        elseif t_distance == .7 && ~length(radii(:,1))==2
            disp("error reading .7 sphere " + string(iFrame))
        end

        if t_distance == 1 && length(radii(:,1))==2
            % find smaller x value for centers 
            [~, pos] = (min(centers(:,1)));     
            t3(iFrame, 'T1_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T1_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T1_y') = num2cell(centers(pos,2));
            [~, pos] = (max(centers(:,1)));         
            t3(iFrame, 'T11_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T11_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T11_y') = num2cell(centers(pos,2));
        elseif t_distance == 1 && ~length(radii(:,1))==2
            disp("error reading 1.0 sphere " + string(iFrame))
        end

        if t_distance == 1.45 && length(radii(:,1))==2
            % find smaller x value for centers 
            [~, pos] = (min(centers(:,1)));     
            t3(iFrame, 'T7_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T7_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T7_y') = num2cell(centers(pos,2));
            [~, pos] = (max(centers(:,1)));         
            t3(iFrame, 'T2_r') = num2cell(radii(pos,1));
            t3(iFrame, 'T2_x') = num2cell(centers(pos,1));
            t3(iFrame, 'T2_y') = num2cell(centers(pos,2));
        elseif t_distance == 1.45 && ~length(radii(:,1))==2
            disp("error reading 1.45 sphere " + string(iFrame))
        end
    end    
end
new_table = t3;
end
% % % when display point cloud draw all detedted targets 
function draw_circles(t3)

    viscircles([t3.T1_x(1) t3.T1_y(1)], t3.T1_r(1),'EdgeColor','b');
    viscircles([t3.T2_x(1) t3.T2_y(1)], t3.T2_r(1),'EdgeColor','r');
    viscircles([t3.T3_x(1) t3.T3_y(1)], t3.T3_r(1),'EdgeColor','y');
    viscircles([t3.T4_x(1) t3.T4_y(1)], t3.T4_r(1),'EdgeColor','g');
    viscircles([t3.T5_x(1) t3.T5_y(1)], t3.T5_r(1),'EdgeColor','b');
    viscircles([t3.T6_x(1) t3.T6_y(1)], t3.T6_r(1),'EdgeColor','m');
    viscircles([t3.T7_x(1) t3.T7_y(1)], t3.T7_r(1),'EdgeColor','g');
    viscircles([t3.T8_x(1) t3.T8_y(1)], t3.T8_r(1),'EdgeColor','r');
    viscircles([t3.T9_x(1) t3.T9_y(1)], t3.T9_r(1),'EdgeColor','y');
    viscircles([t3.T10_x(1) t3.T10_y(1)], t3.T10_r(1),'EdgeColor','m');
    viscircles([t3.T11_x(1) t3.T11_y(1)], t3.T11_r(1),'EdgeColor','g');
end