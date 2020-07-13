% % % %  
% """
% (*)~---------------------------------------------------------------------------
% author: p.wagner@unsw.edu.au / p.wagner@bhvi.org
% 
% 
% find all target positions in point cloud all point clouds availabe in 
%  recording.  
%     data output: all x y positions of all targets sorted 
% 
% dependencies:
%     - royale_LEVEL1_extract_target_data(FileName, disp_pointcloud)
%     - FileName == point cloud in accuracy recording folder 
%     - disp_pointcloud - visualize point cloud (very slow but looks good) 
% ---------------------------------------------------------------------------~(*)
% """
% % %   
recording_fp = 'D:\PupilLabsRecordings\2020_06_11\007';

pc_fp_n = dir(fullfile(recording_fp, 'pointcloud*.rrf'));
for idx = 1:size(pc_fp_n,1)
    
    fp_n = (fullfile(pc_fp_n(idx).folder, pc_fp_n(idx).name));
    disp(fp_n)
    target_data_table = royale_LEVEL1_extract_target_data(fp_n, false);
    writetable(target_data_table, [fp_n, '.csv']);
    if isfile([fp_n, '.csv'])
    	fprintf('* ... file saved!\n');
    else
        fprintf('* ... file not created!\n');
    end
end