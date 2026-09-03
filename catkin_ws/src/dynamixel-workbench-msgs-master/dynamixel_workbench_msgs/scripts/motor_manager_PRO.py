#!/usr/bin/env python
import rospy
import time
from dynamixel_workbench_msgs.srv import DynamixelCommand, DynamixelCommandRequest

def main():
    # Initialize the ROS node
    rospy.init_node('service_client')

    # Wait for the service to become available
    rospy.wait_for_service('/dynamixel_workbench/dynamixel_command')

    try:
        # Create a ROS service proxy
        service_proxy = rospy.ServiceProxy('/dynamixel_workbench/dynamixel_command', DynamixelCommand)

        # Create a service request message
        service_request = DynamixelCommandRequest()
        
        service_request.command = ''
        service_request.id = 4
        service_request.addr_name = 'Goal_Position'
        service_request.value = 0
        # Call the service
        service_response = service_proxy(service_request)
        time.sleep(0.5)
        
        service_request.command = ''
        service_request.id = 2
        service_request.addr_name = 'Goal_Position'
        service_request.value = 1400
        # Call the service
        service_response = service_proxy(service_request)   
        time.sleep(0.5)        
        
        
        service_request.command = ''
        service_request.id = 2
        service_request.addr_name = 'Goal_Position'
        service_request.value = 800
        # Call the service
        service_response = service_proxy(service_request)        
        time.sleep(0.5)
        
        service_request.command = ''
        service_request.id = 2
        service_request.addr_name = 'Goal_Position'
        service_request.value = 1400
        # Call the service
        service_response = service_proxy(service_request)   
        time.sleep(0.5)
        
        service_request.command = ''
        service_request.id = 2
        service_request.addr_name = 'Goal_Position'
        service_request.value = 800
        # Call the service
        service_response = service_proxy(service_request)        
        time.sleep(0.5)
        
        service_request.command = ''
        service_request.id = 2
        service_request.addr_name = 'Goal_Position'
        service_request.value = 1400
        # Call the service
        service_response = service_proxy(service_request)   
        time.sleep(0.5)
        
        service_request.command = ''
        service_request.id = 4
        service_request.addr_name = 'Goal_Position'
        service_request.value = 132
        # Call the service
        service_response = service_proxy(service_request)
        time.sleep(0.5)       
        
        # Process the service response
        if service_response.comm_result:
            rospy.loginfo("Service call succeeded!")
        else:
            rospy.loginfo("Service call failed!")

    except rospy.ServiceException as e:
        rospy.logerr("Service call failed: %s" % str(e))

if __name__ == '__main__':
    main()
