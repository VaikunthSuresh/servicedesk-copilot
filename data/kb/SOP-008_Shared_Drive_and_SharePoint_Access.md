# SOP-008: Shared Drive, SharePoint and Group Access Requests

Owner: Identity & Access Management (IAM)

## Principle
Access is granted to security groups, never to individuals directly. Every request needs approval from the **data owner** of the folder or site, not only the requester's manager.

## Requesting Access
1. The user raises an Access Request in the service portal naming the share path (for example `\\fs01\finance\reports`) or SharePoint site URL.
2. The request is routed to the data owner for approval.
3. After approval, IAM adds the user to the matching security group. Changes take up to 60 minutes to apply; the user must sign out and back in.

## "Access Denied" on a Folder the User Had Before
- Check whether the user changed department recently: group memberships are reviewed on transfer and old ones removed.
- Check the quarterly access review: unconfirmed memberships are removed automatically.

## Sharing Externally
External sharing from SharePoint and OneDrive is blocked for sites labelled Confidential. Users who need to share with a vendor must request a vendor collaboration site.
